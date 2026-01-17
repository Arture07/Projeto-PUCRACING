"""
Módulo de Recepção LoRa - PUCPR Racing

Responsável por:
- Conexão Serial com receptor LoRa (USB)
- Recepção de pacotes binários da Central (Raspberry Pi)
- Desempacotamento da struct enviada pela Central
- Atualização do dashboard em tempo real

Protocolo:
    A Central (Raspberry Pi) envia via LoRa uma struct binária:
    
    struct {
        uint16_t rpm;           // 0-13000
        int8_t temperatura;     // -40 a 125°C
        uint8_t tps;            // 0-100%
        uint16_t lambda;        // 0-2000 (dividir por 1000)
        int16_t steeringAngle;  // -500 a 500 (dividir por 10)
        uint16_t brakePressure; // 0-200 bar
        int16_t accelX;         // -3000 a 3000 (dividir por 1000)
        int16_t accelY;         // -3000 a 3000 (dividir por 1000)
        uint16_t wheelFL;       // 0-300 km/h
        uint16_t wheelFR;
        uint16_t wheelRL;
        uint16_t wheelRR;
        uint16_t suspFL;        // 0-200 mm
        uint16_t suspFR;
        uint16_t suspRL;
        uint16_t suspRR;
        uint32_t timestamp;     // milissegundos desde boot
    } __attribute__((packed));
    
    Total: 36 bytes
"""

import serial
import serial.tools.list_ports
import struct
import threading
import time
from typing import Optional, Dict, Any
from collections import deque

# Constantes do protocolo
PACKET_SIZE = 36  # Tamanho total da struct em bytes
STRUCT_FORMAT = '<HbBHhHhhhHHHHHHHHI'  # Little-endian, campos conforme struct
BAUD_RATE = 115200  # Taxa padrão LoRa
TIMEOUT = 2.0  # Timeout de leitura serial (segundos)

# Marcadores de início/fim de pacote (opcional - se a central usar)
START_MARKER = b'\xAA\x55'  # 0xAA55 - marcador de início
END_MARKER = b'\x55\xAA'    # 0x55AA - marcador de fim


class LoRaReceiver:
    """Gerenciador de recepção LoRa via Serial"""
    
    def __init__(self, port: Optional[str] = None):
        """
        Inicializa o receptor LoRa.
        
        Args:
            port: Porta serial (ex: 'COM3' ou '/dev/ttyUSB0').
                  Se None, tentará detectar automaticamente.
        """
        self.port = port
        self.serial_conn: Optional[serial.Serial] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Buffer de dados recebidos
        self.latest_data: Dict[str, Any] = {}
        self.data_lock = threading.Lock()
        
        # Estatísticas
        self.packets_received = 0
        self.packets_errors = 0
        self.start_time = time.time()
        
        # Buffer circular para cálculo de Hz
        self.rx_times = deque(maxlen=50)
    
    def list_available_ports(self) -> list:
        """Lista portas seriais disponíveis no sistema."""
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]
    
    def auto_detect_port(self) -> Optional[str]:
        """
        Tenta detectar automaticamente a porta do receptor LoRa.
        Procura por dispositivos USB comuns (CH340, FTDI, CP210x).
        """
        ports = serial.tools.list_ports.comports()
        
        # Palavras-chave comuns em receptores LoRa/USB
        keywords = ['CH340', 'FTDI', 'CP210', 'USB', 'Serial']
        
        for port in ports:
            desc = port.description.upper()
            if any(kw.upper() in desc for kw in keywords):
                print(f"[LoRa] Porto detectado: {port.device} ({port.description})")
                return port.device
        
        # Se não encontrar, retorna o primeiro disponível
        if ports:
            print(f"[LoRa] Usando primeiro porto disponível: {ports[0].device}")
            return ports[0].device
        
        return None
    
    def connect(self) -> bool:
        """
        Conecta à porta serial do receptor LoRa.
        
        Returns:
            True se conectou com sucesso, False caso contrário.
        """
        if self.serial_conn and self.serial_conn.is_open:
            print("[LoRa] Já conectado!")
            return True
        
        # Auto-detecção se porta não especificada
        if not self.port:
            self.port = self.auto_detect_port()
        
        if not self.port:
            print("[LoRa] ERRO: Nenhuma porta serial encontrada!")
            return False
        
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=BAUD_RATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=TIMEOUT
            )
            print(f"[LoRa] Conectado em {self.port} @ {BAUD_RATE} baud")
            time.sleep(2)  # Aguarda estabilização da conexão
            self.serial_conn.reset_input_buffer()  # Limpa buffer antigo
            return True
            
        except serial.SerialException as e:
            print(f"[LoRa] ERRO ao conectar: {e}")
            return False
    
    def disconnect(self):
        """Desconecta da porta serial."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("[LoRa] Desconectado")
    
    def unpack_packet(self, raw_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Desempacota a struct binária recebida.
        
        Args:
            raw_data: Bytes brutos do pacote (36 bytes)
        
        Returns:
            Dicionário com dados decodificados ou None se erro
        """
        if len(raw_data) != PACKET_SIZE:
            print(f"[LoRa] Tamanho inválido: {len(raw_data)} bytes (esperado {PACKET_SIZE})")
            return None
        
        try:
            # Desempacota struct
            unpacked = struct.unpack(STRUCT_FORMAT, raw_data)
            
            # Converte para dicionário com nomes legíveis e escalas corretas
            data = {
                'RPM': unpacked[0],
                'Temperatura': unpacked[1],
                'ThrottlePos': unpacked[2],
                'Lambda': unpacked[3] / 1000.0,  # Converte de uint16 para float
                'SteeringAngle': unpacked[4] / 10.0,
                'BrakePressure': unpacked[5],
                'AccelX': unpacked[6] / 1000.0,
                'AccelY': unpacked[7] / 1000.0,
                'WheelSpeed_FL': unpacked[8],
                'WheelSpeed_FR': unpacked[9],
                'WheelSpeed_RL': unpacked[10],
                'WheelSpeed_RR': unpacked[11],
                'SuspensionPos_FL': unpacked[12],
                'SuspensionPos_FR': unpacked[13],
                'SuspensionPos_RL': unpacked[14],
                'SuspensionPos_RR': unpacked[15],
                'timestamp_ms': unpacked[16]
            }
            
            return data
            
        except struct.error as e:
            print(f"[LoRa] Erro ao desempacotar: {e}")
            return None
    
    def read_packet(self) -> Optional[bytes]:
        """
        Lê um pacote completo da serial.
        
        Estratégia:
        1. Se usar marcadores (START/END), busca por eles
        2. Caso contrário, lê exatamente PACKET_SIZE bytes
        
        Returns:
            Bytes do pacote ou None se timeout/erro
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
        
        try:
            # Opção 1: Se a Central usar marcadores START/END
            # (comentar se a Central NÃO enviar marcadores)
            '''
            # Busca marcador de início
            while self.running:
                if self.serial_conn.read(1) == START_MARKER[0]:
                    if self.serial_conn.read(1) == START_MARKER[1]:
                        # Encontrou START_MARKER, lê payload
                        payload = self.serial_conn.read(PACKET_SIZE)
                        # Lê marcador de fim
                        end = self.serial_conn.read(len(END_MARKER))
                        if end == END_MARKER:
                            return payload
            '''
            
            # Opção 2: Leitura direta de bytes (SEM marcadores)
            # Mais simples se a Central enviar pacotes com intervalo fixo
            data = self.serial_conn.read(PACKET_SIZE)
            if len(data) == PACKET_SIZE:
                return data
            
            return None
            
        except serial.SerialException as e:
            print(f"[LoRa] Erro na leitura: {e}")
            return None
    
    def reception_loop(self):
        """Thread principal de recepção de dados."""
        print("[LoRa] Thread de recepção iniciada")
        
        while self.running:
            # Lê pacote
            raw_packet = self.read_packet()
            
            if raw_packet:
                # Desempacota
                data = self.unpack_packet(raw_packet)
                
                if data:
                    # Atualiza dados mais recentes (thread-safe)
                    with self.data_lock:
                        self.latest_data = data
                    
                    self.packets_received += 1
                    self.rx_times.append(time.time())
                    
                    # Debug (comentar em produção)
                    # print(f"[LoRa] RPM={data['RPM']}, Temp={data['Temperatura']}°C")
                else:
                    self.packets_errors += 1
            
            # Pequeno delay para não sobrecarregar CPU
            time.sleep(0.01)  # 10ms = ~100Hz máximo
        
        print("[LoRa] Thread de recepção finalizada")
    
    def start(self) -> bool:
        """
        Inicia recepção em background.
        
        Returns:
            True se iniciou com sucesso
        """
        if self.running:
            print("[LoRa] Já está rodando!")
            return True
        
        if not self.connect():
            return False
        
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self.reception_loop, daemon=True)
        self.thread.start()
        
        print("[LoRa] Recepção iniciada")
        return True
    
    def stop(self):
        """Para a recepção e desconecta."""
        if not self.running:
            return
        
        print("[LoRa] Parando recepção...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=3.0)
        
        self.disconnect()
        print("[LoRa] Recepção parada")
    
    def get_latest_data(self) -> Dict[str, Any]:
        """
        Retorna os dados mais recentes recebidos (thread-safe).
        
        Returns:
            Dicionário com valores dos sensores
        """
        with self.data_lock:
            return self.latest_data.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de recepção."""
        uptime = time.time() - self.start_time
        
        # Calcula Hz baseado nos últimos recebimentos
        hz = 0.0
        if len(self.rx_times) >= 2:
            dt = self.rx_times[-1] - self.rx_times[0]
            if dt > 0:
                hz = (len(self.rx_times) - 1) / dt
        
        return {
            'packets_received': self.packets_received,
            'packets_errors': self.packets_errors,
            'success_rate': (self.packets_received / max(self.packets_received + self.packets_errors, 1)) * 100,
            'uptime_seconds': uptime,
            'current_hz': hz
        }


# ========== Integração com o Dashboard ==========

def start_lora_telemetry(app_instance, port: Optional[str] = None):
    """
    Inicia telemetria LoRa e integra com o dashboard.
    
    Args:
        app_instance: Instância de AppAnalisePUCPR
        port: Porta serial (opcional, auto-detecta se None)
    """
    # Cria receptor
    app_instance.lora_receiver = LoRaReceiver(port=port)
    
    # Inicia recepção
    if app_instance.lora_receiver.start():
        app_instance.is_live_active = True
        app_instance.start_time_live = time.time()
        app_instance.live_data_storage = {'Time': []}
        
        # Atualiza UI
        app_instance.btn_live_toggle.configure(text="⏹️ Parar LoRa", fg_color="#C62828")
        app_instance.lbl_live_status.configure(text=f"Status: LoRa conectado ({app_instance.lora_receiver.port})")
        
        # Inicia loop de atualização da GUI
        app_instance.after(100, lambda: update_lora_gui(app_instance))
        
        return True
    else:
        app_instance.lbl_live_status.configure(text="Status: ERRO ao conectar LoRa")
        return False


def stop_lora_telemetry(app_instance):
    """Para telemetria LoRa."""
    if hasattr(app_instance, 'lora_receiver'):
        app_instance.lora_receiver.stop()
    
    app_instance.is_live_active = False
    app_instance.btn_live_toggle.configure(text="▶️ Iniciar LoRa", fg_color="#D32F2F")
    app_instance.lbl_live_status.configure(text="Status: Parado")


def update_lora_gui(app_instance):
    """
    Atualiza GUI com dados LoRa (chamado a cada 100ms via after).
    """
    if not app_instance.is_live_active:
        return
    
    if not hasattr(app_instance, 'lora_receiver'):
        return
    
    # Pega dados mais recentes
    dados_recentes = app_instance.lora_receiver.get_latest_data()
    
    if dados_recentes:
        # Calcula tempo relativo
        current_time_rel = time.time() - app_instance.start_time_live
        
        # Atualiza armazenamento para gráfico
        if 'Time' not in app_instance.live_data_storage:
            app_instance.live_data_storage['Time'] = []
        app_instance.live_data_storage['Time'].append(current_time_rel)
        
        # Sincroniza canais (mesmo código do telemetry_realtime.py)
        target_len = len(app_instance.live_data_storage['Time'])
        
        canais_para_atualizar = set(app_instance.live_data_storage.keys()) | set(dados_recentes.keys()) | set(app_instance.selected_live_channels)
        canais_para_atualizar.discard('Time')
        
        for canal in canais_para_atualizar:
            if canal not in app_instance.live_data_storage:
                app_instance.live_data_storage[canal] = []
            
            current_len = len(app_instance.live_data_storage[canal])
            missing_steps = target_len - 1 - current_len
            
            if missing_steps > 0:
                app_instance.live_data_storage[canal].extend([0] * missing_steps)
            
            valor = dados_recentes.get(canal, 0)
            app_instance.live_data_storage[canal].append(valor)
        
        # Atualiza estatísticas
        stats = app_instance.lora_receiver.get_statistics()
        app_instance.lbl_live_status.configure(
            text=f"Status: LoRa {stats['current_hz']:.1f} Hz | {stats['packets_received']} pkts | {stats['success_rate']:.1f}% OK"
        )
        
        # Atualiza dashboards (reutiliza função existente)
        from core.telemetry_realtime import _update_dashboard_labels
        _update_dashboard_labels(app_instance, dados_recentes)
        
        # Atualiza gráfico (reutiliza código do live_plotting)
        if not app_instance.live_freeze and len(app_instance.live_data_storage['Time']) > 1:
            app_instance.update_live_plot_style()  # Força redesenho
    
    # Reagenda
    if app_instance.is_live_active:
        app_instance.after(100, lambda: update_lora_gui(app_instance))


# ========== Exemplo de Uso Standalone ==========

if __name__ == "__main__":
    """Teste standalone do receptor LoRa"""
    print("=== Teste do Receptor LoRa ===\n")
    
    # Cria receptor
    receiver = LoRaReceiver()
    
    # Lista portas disponíveis
    print("Portas seriais disponíveis:")
    for device, desc in receiver.list_available_ports():
        print(f"  {device}: {desc}")
    print()
    
    # Inicia recepção
    if receiver.start():
        print("Recebendo dados... (Ctrl+C para parar)\n")
        
        try:
            while True:
                time.sleep(1)
                
                # Pega dados
                data = receiver.get_latest_data()
                stats = receiver.get_statistics()
                
                if data:
                    print(f"[{stats['current_hz']:5.1f} Hz] RPM={data.get('RPM', 0):5d} | "
                          f"Temp={data.get('Temperatura', 0):3d}°C | "
                          f"TPS={data.get('ThrottlePos', 0):3d}% | "
                          f"Brake={data.get('BrakePressure', 0):3d} bar")
                else:
                    print(f"Aguardando dados... ({stats['packets_received']} pacotes recebidos)")
        
        except KeyboardInterrupt:
            print("\n\nParando...")
    
    receiver.stop()
    print("Finalizado!")
