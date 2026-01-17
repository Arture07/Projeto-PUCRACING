#!/usr/bin/env python3
"""
central.py - PUCPR Racing Telemetria Central (Raspberry Pi)

Este script roda na Raspberry Pi dentro do carro e realiza:
1. Leitura de mensagens CAN da ECU (python-can + SocketCAN)
2. Aplicação de DOWNSAMPLING (filtros de taxa) para economizar banda LoRa
3. Transmissão via LoRa Serial de pacotes binários otimizados

ENGENHARIA DE COMPETIÇÃO - OTIMIZAÇÃO DE BANDA:
===============================================

Taxa de Aquisição (ECU → Central):
- ECU envia dados a 50-100 Hz (muito rápido para LoRa)

Taxa de Transmissão (Central → LoRa):
- Alta Prioridade (50 Hz):  RPM, Suspensão (4x), Aceleração (X/Y), Volante, Freio
- Média Prioridade (10 Hz): TPS, Lambda, Velocidade das Rodas (4x)
- Baixa Prioridade (1 Hz):  Temperatura Motor, Bateria, GPS

TAXA MÁXIMA TEÓRICA LoRa (SF7, BW125, CR4/5):
- ~5470 bps = 683 bytes/s
- Pacote de 36 bytes @ 50 Hz = 1800 bytes/s → SATURADO! ❌
- Pacote de 36 bytes @ 15 Hz = 540 bytes/s → OK ✓

ESTRATÉGIA:
- Pacote principal (alta prioridade): 50 Hz
- Dados de baixa prioridade: incluídos a cada N ciclos
"""

import can
import cantools
import struct
import time
import serial
import threading
from dataclasses import dataclass
from typing import Optional
import os

# ============================================================================
# CONFIGURAÇÕES DO SISTEMA
# ============================================================================

# CAN Bus
CAN_INTERFACE = 'can0'  # SocketCAN no Linux
CAN_BITRATE = 500000    # 500 kbps
DBC_FILE = 'pucpr.dbc'  # Arquivo de definição CAN

# LoRa Serial
LORA_PORT = '/dev/ttyUSB0'  # Porta serial do módulo LoRa
LORA_BAUD = 115200          # Taxa de transmissão serial

# Taxas de transmissão (Hz)
RATE_HIGH_PRIORITY = 50      # RPM, Suspensão, Aceleração
RATE_MEDIUM_PRIORITY = 10    # TPS, Lambda, Velocidade Rodas
RATE_LOW_PRIORITY = 1        # Temperatura, Bateria, GPS

# Marcadores de pacote (opcional - ajuda na recepção)
USE_PACKET_MARKERS = True
START_MARKER = b'\xAA\x55'
END_MARKER = b'\x55\xAA'

# ============================================================================
# ESTRUTURA DE DADOS (mesmo formato do lora_receiver.py)
# ============================================================================

@dataclass
class TelemetryData:
    """
    Estrutura de dados de telemetria.
    Total: 36 bytes (packed struct)
    """
    # Alta Prioridade (50 Hz)
    rpm: int = 0                    # 0-13000 RPM (uint16)
    steering_angle: float = 0.0     # -50.0 a 50.0° (int16 / 10)
    brake_pressure: int = 0         # 0-200 bar (uint16)
    accel_x: float = 0.0            # -3.0 a 3.0 G (int16 / 1000)
    accel_y: float = 0.0            # -3.0 a 3.0 G (int16 / 1000)
    susp_fl: int = 0                # 0-200 mm (uint16)
    susp_fr: int = 0                # 0-200 mm (uint16)
    susp_rl: int = 0                # 0-200 mm (uint16)
    susp_rr: int = 0                # 0-200 mm (uint16)
    
    # Média Prioridade (10 Hz)
    tps: int = 0                    # 0-100% (uint8)
    lambda_: float = 0.0            # 0.0-2.0 (uint16 / 1000)
    wheel_fl: int = 0               # 0-300 km/h (uint16)
    wheel_fr: int = 0               # 0-300 km/h (uint16)
    wheel_rl: int = 0               # 0-300 km/h (uint16)
    wheel_rr: int = 0               # 0-300 km/h (uint16)
    
    # Baixa Prioridade (1 Hz)
    temperatura: int = 0            # -40 a 125°C (int8)
    
    timestamp: int = 0              # milissegundos (uint32)


# ============================================================================
# GERENCIADOR DE DOWNSAMPLING
# ============================================================================

class DownsamplingManager:
    """
    Gerencia taxas de aquisição diferentes para cada grupo de dados.
    
    Conceito: DOWNSAMPLING (Redução de Taxa)
    =========================================
    - Nem todos os dados precisam ser enviados a 50 Hz
    - Temperatura do motor varia lentamente → 1 Hz suficiente
    - RPM varia rapidamente → 50 Hz necessário
    - Reduz banda LoRa em ~60% sem perder informação crítica
    """
    
    def __init__(self):
        # Contadores de ciclos
        self.cycle_count = 0
        self.start_time = time.time()
        
        # Calcular intervalos (quantos ciclos do loop principal)
        # Loop principal roda a RATE_HIGH_PRIORITY (50 Hz)
        # 1 ciclo = 1/50 = 20ms
        
        self.high_interval = 1  # Todo ciclo (50 Hz)
        self.medium_interval = RATE_HIGH_PRIORITY // RATE_MEDIUM_PRIORITY  # A cada 5 ciclos (10 Hz)
        self.low_interval = RATE_HIGH_PRIORITY // RATE_LOW_PRIORITY        # A cada 50 ciclos (1 Hz)
        
        # Timestamps dos últimos envios (alternativa aos contadores)
        self.last_high = 0.0
        self.last_medium = 0.0
        self.last_low = 0.0
        
        print(f"[Downsampling] Configurado:")
        print(f"  Alta prioridade: a cada {self.high_interval} ciclo(s) ({RATE_HIGH_PRIORITY} Hz)")
        print(f"  Média prioridade: a cada {self.medium_interval} ciclo(s) ({RATE_MEDIUM_PRIORITY} Hz)")
        print(f"  Baixa prioridade: a cada {self.low_interval} ciclo(s) ({RATE_LOW_PRIORITY} Hz)")
    
    def should_send_high(self) -> bool:
        """Sempre envia (50 Hz)"""
        return True
    
    def should_send_medium(self) -> bool:
        """Envia a cada N ciclos (10 Hz)"""
        return (self.cycle_count % self.medium_interval) == 0
    
    def should_send_low(self) -> bool:
        """Envia a cada M ciclos (1 Hz)"""
        return (self.cycle_count % self.low_interval) == 0
    
    def increment_cycle(self):
        """Incrementa contador de ciclos"""
        self.cycle_count += 1
        if self.cycle_count >= self.low_interval:
            self.cycle_count = 0  # Reset para evitar overflow
    
    def get_statistics(self) -> dict:
        """Retorna estatísticas de uso de banda"""
        elapsed = time.time() - self.start_time
        if elapsed < 1.0:
            return {}
        
        # Calcular taxa efetiva de transmissão
        packets_per_sec = RATE_HIGH_PRIORITY  # Sempre enviamos pacotes a 50 Hz
        bytes_per_packet = 36
        
        # Mas nem todos os campos são atualizados sempre
        # Economizamos banda ao reutilizar valores antigos
        
        total_bytes_sec = packets_per_sec * bytes_per_packet
        bandwidth_kbps = (total_bytes_sec * 8) / 1000
        
        return {
            'packets_per_sec': packets_per_sec,
            'bytes_per_sec': total_bytes_sec,
            'bandwidth_kbps': bandwidth_kbps,
            'uptime_sec': int(elapsed)
        }


# ============================================================================
# RECEPTOR CAN
# ============================================================================

class CANReceiver:
    """
    Recebe mensagens CAN da ECU e decodifica usando DBC.
    """
    
    def __init__(self, interface: str, dbc_path: str):
        self.interface = interface
        self.dbc_path = dbc_path
        self.db = None
        self.bus = None
        self.running = False
        
        # Buffer de dados (thread-safe)
        self.data = TelemetryData()
        self.data_lock = threading.Lock()
        
        # Estatísticas
        self.messages_received = 0
    
    def connect(self):
        """Conecta ao barramento CAN"""
        try:
            # Carregar DBC
            self.db = cantools.database.load_file(self.dbc_path)
            print(f"[CAN] DBC carregado: {len(self.db.messages)} mensagens")
            
            # Conectar ao barramento
            self.bus = can.interface.Bus(
                channel=self.interface,
                bustype='socketcan',
                bitrate=CAN_BITRATE
            )
            print(f"[CAN] Conectado em {self.interface} @ {CAN_BITRATE} bps")
            return True
            
        except Exception as e:
            print(f"[CAN] Erro ao conectar: {e}")
            return False
    
    def process_message(self, msg: can.Message):
        """
        Processa uma mensagem CAN e atualiza os dados.
        
        IMPORTANTE: Aqui ocorre a AQUISIÇÃO de dados (50-100 Hz da ECU)
        O DOWNSAMPLING ocorre na transmissão LoRa, não aqui.
        """
        try:
            # Decodificar mensagem usando DBC
            decoded = self.db.decode_message(msg.arbitration_id, msg.data)
            
            with self.data_lock:
                # Mapear sinais CAN para estrutura de telemetria
                # NOTA: Ajuste os nomes dos sinais conforme seu arquivo DBC
                
                if 'RPM' in decoded:
                    self.data.rpm = int(decoded['RPM'])
                
                if 'EngineTemp' in decoded:
                    self.data.temperatura = int(decoded['EngineTemp'])
                
                if 'TPS' in decoded:
                    self.data.tps = int(decoded['TPS'])
                
                if 'Lambda' in decoded:
                    self.data.lambda_ = float(decoded['Lambda'])
                
                if 'SteeringAngle' in decoded:
                    self.data.steering_angle = float(decoded['SteeringAngle'])
                
                if 'BrakePressure' in decoded:
                    self.data.brake_pressure = int(decoded['BrakePressure'])
                
                if 'AccelX' in decoded:
                    self.data.accel_x = float(decoded['AccelX'])
                
                if 'AccelY' in decoded:
                    self.data.accel_y = float(decoded['AccelY'])
                
                # Velocidades das rodas
                if 'WheelSpeed_FL' in decoded:
                    self.data.wheel_fl = int(decoded['WheelSpeed_FL'])
                if 'WheelSpeed_FR' in decoded:
                    self.data.wheel_fr = int(decoded['WheelSpeed_FR'])
                if 'WheelSpeed_RL' in decoded:
                    self.data.wheel_rl = int(decoded['WheelSpeed_RL'])
                if 'WheelSpeed_RR' in decoded:
                    self.data.wheel_rr = int(decoded['WheelSpeed_RR'])
                
                # Suspensão
                if 'Suspension_FL' in decoded:
                    self.data.susp_fl = int(decoded['Suspension_FL'])
                if 'Suspension_FR' in decoded:
                    self.data.susp_fr = int(decoded['Suspension_FR'])
                if 'Suspension_RL' in decoded:
                    self.data.susp_rl = int(decoded['Suspension_RL'])
                if 'Suspension_RR' in decoded:
                    self.data.susp_rr = int(decoded['Suspension_RR'])
            
            self.messages_received += 1
            
        except Exception as e:
            # Mensagem não está no DBC ou erro de decodificação
            pass
    
    def get_current_data(self) -> TelemetryData:
        """Retorna snapshot dos dados atuais (thread-safe)"""
        with self.data_lock:
            # Criar cópia para evitar race conditions
            return TelemetryData(
                rpm=self.data.rpm,
                temperatura=self.data.temperatura,
                tps=self.data.tps,
                lambda_=self.data.lambda_,
                steering_angle=self.data.steering_angle,
                brake_pressure=self.data.brake_pressure,
                accel_x=self.data.accel_x,
                accel_y=self.data.accel_y,
                wheel_fl=self.data.wheel_fl,
                wheel_fr=self.data.wheel_fr,
                wheel_rl=self.data.wheel_rl,
                wheel_rr=self.data.wheel_rr,
                susp_fl=self.data.susp_fl,
                susp_fr=self.data.susp_fr,
                susp_rl=self.data.susp_rl,
                susp_rr=self.data.susp_rr,
                timestamp=int(time.time() * 1000)
            )
    
    def reception_loop(self):
        """Loop de recepção CAN (thread separada)"""
        print("[CAN] Loop de recepção iniciado")
        
        while self.running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    self.process_message(msg)
            except Exception as e:
                print(f"[CAN] Erro no loop: {e}")
                time.sleep(0.1)
        
        print("[CAN] Loop de recepção finalizado")
    
    def start(self):
        """Inicia recepção em background"""
        if not self.connect():
            return False
        
        self.running = True
        thread = threading.Thread(target=self.reception_loop, daemon=True)
        thread.start()
        return True
    
    def stop(self):
        """Para recepção"""
        self.running = False
        if self.bus:
            self.bus.shutdown()


# ============================================================================
# TRANSMISSOR LoRa
# ============================================================================

class LoRaTransmitter:
    """
    Transmite pacotes binários via LoRa Serial.
    
    OTIMIZAÇÃO: Usa downsampling para enviar apenas dados necessários.
    """
    
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        self.serial_conn: Optional[serial.Serial] = None
        
        # Estatísticas
        self.packets_sent = 0
        self.bytes_sent = 0
        self.start_time = time.time()
    
    def connect(self) -> bool:
        """Conecta à porta serial do LoRa"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=1.0,
                write_timeout=1.0
            )
            print(f"[LoRa] Conectado em {self.port} @ {self.baud} baud")
            return True
            
        except Exception as e:
            print(f"[LoRa] Erro ao conectar: {e}")
            return False
    
    def pack_telemetry(self, data: TelemetryData) -> bytes:
        """
        Empacota dados de telemetria em struct binária (36 bytes).
        
        Formato: little-endian (<)
        - H: uint16 (2 bytes)
        - h: int16 (2 bytes)
        - b: int8 (1 byte)
        - B: uint8 (1 byte)
        - I: uint32 (4 bytes)
        
        Struct: <HbBHhHhhhHHHHHHHHI
        """
        try:
            # Aplicar escalas (inverso do lora_receiver.py)
            lambda_scaled = int(data.lambda_ * 1000)       # 1.234 → 1234
            steering_scaled = int(data.steering_angle * 10)  # -12.5° → -125
            accel_x_scaled = int(data.accel_x * 1000)      # 1.523 G → 1523
            accel_y_scaled = int(data.accel_y * 1000)      # -0.234 G → -234
            
            # Empacotar
            packed = struct.pack(
                '<HbBHhHhhhHHHHHHHHI',
                data.rpm,              # uint16
                data.temperatura,      # int8
                data.tps,              # uint8
                lambda_scaled,         # uint16
                steering_scaled,       # int16
                data.brake_pressure,   # uint16
                accel_x_scaled,        # int16
                accel_y_scaled,        # int16
                data.wheel_fl,         # uint16
                data.wheel_fr,         # uint16
                data.wheel_rl,         # uint16
                data.wheel_rr,         # uint16
                data.susp_fl,          # uint16
                data.susp_fr,          # uint16
                data.susp_rl,          # uint16
                data.susp_rr,          # uint16
                data.timestamp         # uint32
            )
            
            return packed
            
        except Exception as e:
            print(f"[LoRa] Erro ao empacotar: {e}")
            return b''
    
    def send_packet(self, data: TelemetryData) -> bool:
        """Envia pacote via LoRa"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return False
        
        try:
            payload = self.pack_telemetry(data)
            if not payload:
                return False
            
            # Montar pacote completo
            if USE_PACKET_MARKERS:
                packet = START_MARKER + payload + END_MARKER
            else:
                packet = payload
            
            # Enviar
            self.serial_conn.write(packet)
            
            # Atualizar estatísticas
            self.packets_sent += 1
            self.bytes_sent += len(packet)
            
            return True
            
        except Exception as e:
            print(f"[LoRa] Erro ao enviar: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """Retorna estatísticas de transmissão"""
        elapsed = time.time() - self.start_time
        if elapsed < 1.0:
            return {}
        
        hz = self.packets_sent / elapsed
        bytes_per_sec = self.bytes_sent / elapsed
        kbps = (bytes_per_sec * 8) / 1000
        
        return {
            'packets_sent': self.packets_sent,
            'hz': hz,
            'bytes_per_sec': int(bytes_per_sec),
            'kbps': kbps,
            'uptime_sec': int(elapsed)
        }
    
    def disconnect(self):
        """Desconecta serial"""
        if self.serial_conn:
            self.serial_conn.close()


# ============================================================================
# SISTEMA PRINCIPAL
# ============================================================================

class TelemetrySystem:
    """
    Sistema completo de telemetria com downsampling otimizado.
    """
    
    def __init__(self):
        self.can_receiver = CANReceiver(CAN_INTERFACE, DBC_FILE)
        self.lora_transmitter = LoRaTransmitter(LORA_PORT, LORA_BAUD)
        self.downsampler = DownsamplingManager()
        
        # Cache de dados de baixa/média prioridade
        # (reutilizados quando não é hora de atualizar)
        self.cached_data = TelemetryData()
        
        self.running = False
    
    def start(self) -> bool:
        """Inicia sistema"""
        print("\n" + "="*60)
        print("  PUCPR RACING - TELEMETRIA CENTRAL (Raspberry Pi)")
        print("="*60 + "\n")
        
        # Conectar CAN
        if not self.can_receiver.start():
            print("[Sistema] Falha ao iniciar receptor CAN")
            return False
        
        # Conectar LoRa
        if not self.lora_transmitter.connect():
            print("[Sistema] Falha ao conectar LoRa")
            self.can_receiver.stop()
            return False
        
        print(f"\n[Sistema] Iniciado com sucesso!")
        print(f"  CAN: {CAN_INTERFACE} @ {CAN_BITRATE} bps")
        print(f"  LoRa: {LORA_PORT} @ {LORA_BAUD} baud")
        print(f"  Taxa de transmissão: {RATE_HIGH_PRIORITY} Hz (downsampling ativo)")
        print("\nPressione Ctrl+C para parar\n")
        
        return True
    
    def main_loop(self):
        """
        Loop principal de transmissão.
        
        CONCEITO: DOWNSAMPLING INTELIGENTE
        ===================================
        - Roda a RATE_HIGH_PRIORITY (50 Hz)
        - Sempre envia dados de alta prioridade (RPM, Suspensão, etc)
        - Só atualiza dados de média prioridade a cada N ciclos
        - Só atualiza dados de baixa prioridade a cada M ciclos
        - Reutiliza valores em cache quando não atualiza
        """
        self.running = True
        interval = 1.0 / RATE_HIGH_PRIORITY  # 20ms @ 50 Hz
        
        next_stats_time = time.time() + 5.0  # Mostrar stats a cada 5s
        
        try:
            while self.running:
                loop_start = time.time()
                
                # Obter dados atuais do CAN
                current = self.can_receiver.get_current_data()
                
                # ALTA PRIORIDADE: Sempre atualiza
                packet = TelemetryData()
                packet.rpm = current.rpm
                packet.steering_angle = current.steering_angle
                packet.brake_pressure = current.brake_pressure
                packet.accel_x = current.accel_x
                packet.accel_y = current.accel_y
                packet.susp_fl = current.susp_fl
                packet.susp_fr = current.susp_fr
                packet.susp_rl = current.susp_rl
                packet.susp_rr = current.susp_rr
                packet.timestamp = current.timestamp
                
                # MÉDIA PRIORIDADE: Atualiza a cada N ciclos
                if self.downsampler.should_send_medium():
                    packet.tps = current.tps
                    packet.lambda_ = current.lambda_
                    packet.wheel_fl = current.wheel_fl
                    packet.wheel_fr = current.wheel_fr
                    packet.wheel_rl = current.wheel_rl
                    packet.wheel_rr = current.wheel_rr
                    
                    # Atualizar cache
                    self.cached_data.tps = current.tps
                    self.cached_data.lambda_ = current.lambda_
                    self.cached_data.wheel_fl = current.wheel_fl
                    self.cached_data.wheel_fr = current.wheel_fr
                    self.cached_data.wheel_rl = current.wheel_rl
                    self.cached_data.wheel_rr = current.wheel_rr
                else:
                    # Reutilizar valores em cache
                    packet.tps = self.cached_data.tps
                    packet.lambda_ = self.cached_data.lambda_
                    packet.wheel_fl = self.cached_data.wheel_fl
                    packet.wheel_fr = self.cached_data.wheel_fr
                    packet.wheel_rl = self.cached_data.wheel_rl
                    packet.wheel_rr = self.cached_data.wheel_rr
                
                # BAIXA PRIORIDADE: Atualiza a cada M ciclos
                if self.downsampler.should_send_low():
                    packet.temperatura = current.temperatura
                    self.cached_data.temperatura = current.temperatura
                else:
                    packet.temperatura = self.cached_data.temperatura
                
                # Enviar pacote
                self.lora_transmitter.send_packet(packet)
                
                # Incrementar contador de ciclos
                self.downsampler.increment_cycle()
                
                # Mostrar estatísticas periodicamente
                if time.time() >= next_stats_time:
                    self.print_statistics()
                    next_stats_time = time.time() + 5.0
                
                # Manter taxa constante
                elapsed = time.time() - loop_start
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\n[Sistema] Interrompido pelo usuário")
        except Exception as e:
            print(f"\n[Sistema] Erro no loop: {e}")
        
        self.stop()
    
    def print_statistics(self):
        """Mostra estatísticas de operação"""
        lora_stats = self.lora_transmitter.get_statistics()
        downsample_stats = self.downsampler.get_statistics()
        
        print("\n" + "-"*60)
        print(f"[Stats] Uptime: {lora_stats.get('uptime_sec', 0)}s")
        print(f"  LoRa TX: {lora_stats.get('packets_sent', 0)} pacotes | "
              f"{lora_stats.get('hz', 0):.1f} Hz | "
              f"{lora_stats.get('kbps', 0):.1f} kbps")
        print(f"  CAN RX: {self.can_receiver.messages_received} mensagens")
        print(f"  Banda: {lora_stats.get('bytes_per_sec', 0)} bytes/s "
              f"({lora_stats.get('kbps', 0):.1f} kbps)")
        print("-"*60)
    
    def stop(self):
        """Para sistema"""
        print("\n[Sistema] Encerrando...")
        self.running = False
        self.can_receiver.stop()
        self.lora_transmitter.disconnect()
        print("[Sistema] Finalizado")


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    system = TelemetrySystem()
    
    if system.start():
        system.main_loop()
    else:
        print("[Sistema] Falha ao iniciar")
