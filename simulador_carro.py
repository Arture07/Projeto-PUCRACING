import can
import time
import math
import struct
import random

# --- CONFIGURAÇÃO DE FÍSICA ---
class CarroDeCorrida:
    def __init__(self):
        # Estados
        self.rpm = 1000.0 # Marcha lenta
        self.velocidade_kmh = 0.0
        self.gear = 1
        self.throttle_pos = 0.0 # 0-100
        self.brake_pressure = 0.0 # 0-50 bar
        self.steering_angle = 0.0 # -360 a 360
        self.temp_motor = 85.0
        
        # Física básica
        self.max_rpm = 12000
        self.idle_rpm = 1500
        self.pneu_radius = 0.3 # metros
        self.mass = 250 # kg (FSAE)
        
        # Posição (Simulação de volta)
        self.distance = 0.0
        self.accel_x = 0.0
        self.accel_y = 0.0

    def update(self, dt):
        # 1. Simula Driver Inputs (Automático)
        t = time.time()
        
        # Acelerador: Acelera em retas, solta em curvas
        # Simula uma pista com curvas a cada 10-15 segundos
        section_time = t % 15
        
        if section_time < 8: # Reta
            target_throttle = 100
            target_brake = 0
            target_steer = 0 + random.uniform(-2, 2) # Vibração volante
        elif section_time < 10: # Freada
            target_throttle = 0
            target_brake = 40
            target_steer = 0
        else: # Curva
            target_throttle = 60
            target_brake = 0
            # Senoidal suave para curva
            target_steer = 90 * math.sin((section_time - 10) * 1.5) 
        
        # Suavização dos inputs (Inercia do piloto)
        self.throttle_pos += (target_throttle - self.throttle_pos) * 0.2
        self.brake_pressure += (target_brake - self.brake_pressure) * 0.2
        self.steering_angle += (target_steer - self.steering_angle) * 0.1
        
        # 2. Modelo Motor
        # Se acelerador > 0, RPM sobe. Se freio, cai rapido. Se nada, cai lento (freio motor)
        rpm_growth = (self.throttle_pos / 100) * 8000 # Potencia
        rpm_drag = (self.rpm / 12000) * 2000 # Atrito interno
        rpm_braking = (self.brake_pressure / 50) * 10000 if self.brake_pressure > 1 else 0
        
        delta_rpm = (rpm_growth - rpm_drag - rpm_braking) * dt
        self.rpm += delta_rpm
        
        # Limitador
        if self.rpm > self.max_rpm: self.rpm = self.max_rpm
        if self.rpm < self.idle_rpm: self.rpm = self.idle_rpm
        
        # 3. Transmissão (Simplificada CVT/Fixed Ratio para demo)
        # Velocidade depende do RPM e Marcha (ficticia aqui)
        ratio = 0.015 # Razão RPM -> KMH
        self.velocidade_kmh = self.rpm * ratio
        
        # 4. Forças G (IMU)
        # Accel Longitudinal = dV/dt + gravidade se tiver inclinação
        # dV em m/s
        v_ms = self.velocidade_kmh / 3.6
        vel_antiga_ms = (self.velocidade_kmh - (delta_rpm * ratio)) / 3.6
        if dt > 0:
            self.accel_x = (v_ms - vel_antiga_ms) / dt / 9.81 # em G
        
        # Accel Lateral = v^2 / r
        # Raio da curva depende do esterçamento.
        # Ackermann simplificado: r = entre_eixos / tan(steer)
        # Steer impacta accel Y
        if abs(self.steering_angle) > 5 and self.velocidade_kmh > 10:
             # Fórmula empírica para simular G lateral realista
            self.accel_y = (self.steering_angle / 180) * (self.velocidade_kmh / 50)**2
        else:
            self.accel_y = 0.0
            
        # Adiciona ruído de vibração do motor/pista
        vibration = (self.rpm / 12000) * 0.1
        self.accel_x += random.uniform(-vibration, vibration)
        self.accel_y += random.uniform(-vibration, vibration)
        
        # Temperatura sobe com RPM, desce com tempo (refrigeração)
        self.temp_motor += (self.rpm * 0.0001 - (self.temp_motor - 80)*0.1) * dt

# --- SETUP CAN ---
print("=== SIMULADOR FÍSICO PUCPR RACING ===")
print("Iniciando física veicular avançada...")

bus = None
try:
    bus = can.interface.Bus(channel='239.0.0.1', interface='udp_multicast')
except Exception as e:
    print(f"Erro ao abrir CAN: {e}")
    exit(1)

carro = CarroDeCorrida()

try:
    last_time = time.time()
    
    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        carro.update(dt) # 0.05s ideal
        
        # --- ENVIAR PACOTES CAN ---
        
        # 1. MOTOR (0x100)
        # RPM(2), Temp(1), TPS(1), Lambda(1)
        # Lambda varia rico/pobre aleatoriamente perto de 1.00
        # Lambda escala: 0.01 por bit (0-255 = 0.00-2.55)
        lam_val = int(100 * (1.0 + random.uniform(-0.1, 0.1))) if carro.throttle_pos > 0 else 100
        lam_val = max(0, min(255, lam_val))  # Clamp 0-255
        data_motor = struct.pack('<HBBB', int(carro.rpm), int(carro.temp_motor), int(carro.throttle_pos), lam_val) + b'\x00\x00\x00'
        bus.send(can.Message(arbitration_id=256, data=data_motor, is_extended_id=False))
        
        # 2. RODAS (0x110)
        # Velocidade com leve diferença nas curvas (diferencial)
        ws = int(carro.velocidade_kmh)
        diff = int(carro.accel_y * 10) # Diferença baseada na curva
        data_rodas = struct.pack('<BBBB', ws, ws, max(0, ws-diff), max(0, ws+diff)) + b'\x00\x00\x00\x00'
        bus.send(can.Message(arbitration_id=272, data=data_rodas, is_extended_id=False))
        
        # 3. SUSPENSÃO (0x200)
        # Comprime com freio (dive), levanta com aceleração (squat), inclina com curva (roll)
        base_susp = 100 # mm
        dive = carro.accel_x * 20 # Frente desce com freio (-accel_x) -> Ops, accel_x negativo é freio
        roll = carro.accel_y * 15
        
        # Front Left
        s_fl = int(base_susp + dive + roll + random.uniform(-2,2))
        s_fr = int(base_susp + dive - roll + random.uniform(-2,2))
        s_rl = int(base_susp - dive + roll + random.uniform(-2,2))
        s_rr = int(base_susp - dive - roll + random.uniform(-2,2))
        # Clamp 0-255
        s_fl = max(0, min(255, s_fl)); s_fr = max(0, min(255, s_fr))
        s_rl = max(0, min(255, s_rl)); s_rr = max(0, min(255, s_rr))
        
        data_susp = struct.pack('<BBBB', s_fl, s_fr, s_rl, s_rr) + b'\x00\x00\x00\x00'
        bus.send(can.Message(arbitration_id=512, data=data_susp, is_extended_id=False))
        
        # 4. DIREÇÃO (0x120) Steering(2), Brake(1)
        # Steering x10 (0.1 deg/bit)
        steer_packed = int(carro.steering_angle * 10) 
        brake_packed = int(carro.brake_pressure * 5) # 0-50 bar -> 0-250 byte
        data_dir = struct.pack('<hB', steer_packed, brake_packed) + b'\x00\x00\x00\x00\x00'
        bus.send(can.Message(arbitration_id=288, data=data_dir, is_extended_id=False))

        # 5. IMU (0x300) AccelX(2), AccelY(2)
        # Factor 0.001 -> x1000
        ax_packed = int(carro.accel_x * 1000)
        ay_packed = int(carro.accel_y * 1000)
        data_imu = struct.pack('<hh', ax_packed, ay_packed) + b'\x00\x00\x00\x00'
        bus.send(can.Message(arbitration_id=768, data=data_imu, is_extended_id=False))
        
        # Debug (menos frequente para não poluir)
        # if int(current_time * 10) % 10 == 0:
        #    print(f"RPM: {int(carro.rpm)} | KM/H: {int(carro.velocidade_kmh)} | G-Lat: {carro.accel_y:.2f}")

        time.sleep(0.05) # 20Hz Update Rate (Mais fluido)

except KeyboardInterrupt:
    print("Simulação Encerrada.")