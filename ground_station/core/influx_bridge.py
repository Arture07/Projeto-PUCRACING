"""
Bridge assíncrono para espelhar telemetria em tempo real no InfluxDB.

Objetivo:
- Não bloquear o loop da GUI
- Permitir uso opcional (enable/disable por INI)
- Publicar pontos com tags de sessão e fonte
"""

from __future__ import annotations

import configparser
import importlib
import queue
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

from config_manager import CONFIG_FILE

try:
    influx_module = importlib.import_module("influxdb_client")
    InfluxDBClient = influx_module.InfluxDBClient
    Point = influx_module.Point
    WriteOptions = influx_module.WriteOptions
except Exception:
    InfluxDBClient = None
    Point = None
    WriteOptions = None


class InfluxRealtimeBridge:
    """Writer assíncrono de telemetria para InfluxDB."""

    def __init__(self):
        self.enabled = False
        self.available = InfluxDBClient is not None
        self.url = ""
        self.token = ""
        self.org = ""
        self.bucket = ""
        self.measurement = "telemetry_live"
        self.flush_interval_ms = 50
        self.max_queue_size = 2000

        self.session_id = ""
        self.source = "simulator"

        self._queue: Optional[queue.Queue] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._client = None
        self._write_api = None

        self._dropped = 0
        self._written = 0
        self._errors = 0

        self._load_config()

    def _load_config(self) -> None:
        config = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=("#", ";"))
        try:
            config.read(CONFIG_FILE)
            section = config["INFLUXDB"] if "INFLUXDB" in config else {}
            self.enabled = str(section.get("enabled", "false")).strip().lower() in ("1", "true", "yes", "on")
            self.url = str(section.get("url", "http://localhost:8086")).strip()
            self.token = str(section.get("token", "")).strip()
            self.org = str(section.get("org", "pucpr-racing")).strip()
            self.bucket = str(section.get("bucket", "telemetry")).strip()
            self.measurement = str(section.get("measurement", "telemetry_live")).strip() or "telemetry_live"
            self.flush_interval_ms = int(str(section.get("flush_interval_ms", "50")).strip())
            self.max_queue_size = int(str(section.get("max_queue_size", "2000")).strip())
        except Exception:
            self.enabled = False

    @property
    def active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, source: str = "simulator") -> bool:
        if not self.enabled or not self.available:
            return False

        if not self.url or not self.token or not self.org or not self.bucket:
            return False

        self.source = source
        self.session_id = datetime.utcnow().strftime("session_%Y%m%d_%H%M%S")
        self._queue = queue.Queue(maxsize=max(100, self.max_queue_size))
        self._stop_event.clear()

        try:
            self._client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self._write_api = self._client.write_api(
                write_options=WriteOptions(
                    batch_size=1,
                    flush_interval=max(20, self.flush_interval_ms),
                    jitter_interval=0,
                    retry_interval=1000,
                    max_retries=3,
                    max_retry_delay=5000,
                    exponential_base=2,
                )
            )
        except Exception:
            self._client = None
            self._write_api = None
            return False

        self._thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._thread = None

        try:
            if self._write_api is not None:
                self._write_api.flush()
                self._write_api.close()
        except Exception:
            pass

        try:
            if self._client is not None:
                self._client.close()
        except Exception:
            pass

        self._write_api = None
        self._client = None

    def publish(self, data: Dict[str, Any], timestamp_ns: Optional[int] = None) -> None:
        if not self.active or self._queue is None:
            return

        if not data:
            return

        fields: Dict[str, float] = {}
        for key, value in data.items():
            if key in ("Time", "timestamp_ms"):
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                fields[key] = float(value)

        if not fields:
            return

        payload = {
            "fields": fields,
            "ts_ns": int(timestamp_ns if timestamp_ns is not None else time.time_ns()),
        }

        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            self._dropped += 1

    def _writer_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._queue is None:
                time.sleep(0.05)
                continue

            try:
                payload = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                point = Point(self.measurement).tag("session_id", self.session_id).tag("source", self.source)
                for field_name, value in payload["fields"].items():
                    point = point.field(field_name, value)
                point = point.time(payload["ts_ns"])
                self._write_api.write(bucket=self.bucket, org=self.org, record=point)
                self._written += 1
            except Exception:
                self._errors += 1

    def get_status(self) -> Dict[str, Any]:
        qsize = self._queue.qsize() if self._queue is not None else 0
        return {
            "enabled": self.enabled,
            "available": self.available,
            "active": self.active,
            "session_id": self.session_id,
            "source": self.source,
            "queue_size": qsize,
            "written": self._written,
            "dropped": self._dropped,
            "errors": self._errors,
        }


def ensure_influx_bridge(app_instance, source: str) -> None:
    bridge = getattr(app_instance, "influx_bridge", None)
    if bridge is None:
        bridge = InfluxRealtimeBridge()
        app_instance.influx_bridge = bridge

    if not bridge.active:
        started = bridge.start(source=source)
        app_instance.influx_session_id = bridge.session_id if started else ""


def stop_influx_bridge(app_instance) -> None:
    bridge = getattr(app_instance, "influx_bridge", None)
    if bridge is None:
        return
    bridge.stop()


def publish_influx(app_instance, data: Dict[str, Any], timestamp_ns: Optional[int] = None) -> None:
    bridge = getattr(app_instance, "influx_bridge", None)
    if bridge is None:
        return
    bridge.publish(data, timestamp_ns=timestamp_ns)
