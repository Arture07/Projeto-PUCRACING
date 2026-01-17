# 🔧 Código de Exemplo para ECU - Alta Resolução

## 📋 Visão Geral

Este documento mostra como **modificar o firmware da ECU** para enviar dados com a **nova resolução** definida no arquivo DBC.

**IMPORTANTE**: Ao mudar o `Factor` no DBC, a ECU também precisa enviar valores escalados corretamente!

---

## 🎯 Conceito de Escala

### Exemplo: Temperatura

**DBC Antigo**:
```dbc
SG_ Temperatura : 16|8@1+ (1,0) [0|150] "C" Central
```
- Factor = **1**
- ECU envia: `85` → Ground Station recebe: `85 × 1 = 85°C` ✅

**DBC Novo (Alta Resolução)**:
```dbc
SG_ Temperatura : 16|16@1+ (0.1,-40) [-40|150] "C" Central
```
- Factor = **0.1**
- Offset = **-40**
- Fórmula: `Valor Real = (Valor CAN × 0.1) + (-40)`

**Se a ECU continuar enviando `85`**:
- Ground Station recebe: `(85 × 0.1) + (-40) = -31.5°C` ❌ **ERRADO!**

**ECU deve enviar**: `(85 - (-40)) / 0.1 = 1250`
- Ground Station recebe: `(1250 × 0.1) + (-40) = 85°C` ✅ **CORRETO!**

---

## 💻 Código Arduino/C++ (Exemplo)

### Estrutura CAN Básica

```cpp
#include <mcp_can.h>
#include <SPI.h>

// Configuração CAN
#define CAN_CS_PIN 10
MCP_CAN CAN(CAN_CS_PIN);

// IDs das mensagens (mesmo do DBC)
#define CAN_ID_MOTOR 0x100       // 256 decimal
#define CAN_ID_RODAS 0x110       // 272 decimal
#define CAN_ID_SUSPENSAO 0x200   // 512 decimal
#define CAN_ID_DIRECAO 0x120     // 288 decimal
#define CAN_ID_IMU 0x300         // 768 decimal

void setup() {
    Serial.begin(115200);
    
    // Inicializar CAN a 500 kbps
    if (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) == CAN_OK) {
        Serial.println("CAN OK!");
        CAN.setMode(MCP_NORMAL);
    } else {
        Serial.println("CAN FALHOU!");
    }
}
```

---

### Função para Escalar e Enviar Temperatura

```cpp
/**
 * Envia temperatura do motor via CAN.
 * 
 * DBC: SG_ Temperatura : 16|16@1+ (0.1,-40) [-40|150] "C" Central
 * 
 * @param temp_celsius Temperatura real em °C (ex: 85.2)
 */
void sendTemperature(float temp_celsius) {
    // Aplicar fórmula inversa: (Valor - Offset) / Factor
    // (85.2 - (-40)) / 0.1 = 125.2 / 0.1 = 1252
    int16_t temp_scaled = (int16_t)((temp_celsius - (-40.0)) / 0.1);
    
    // Criar array de dados (8 bytes para mensagem Motor)
    uint8_t data[8];
    
    // Byte 0-1: RPM (uint16, big-endian)
    uint16_t rpm = readRPM();
    data[0] = (rpm >> 8) & 0xFF;  // MSB
    data[1] = rpm & 0xFF;          // LSB
    
    // Byte 2-3: Temperatura (uint16, big-endian)
    data[2] = (temp_scaled >> 8) & 0xFF;  // MSB
    data[3] = temp_scaled & 0xFF;          // LSB
    
    // Byte 4: TPS (uint8, 0.1% de resolução)
    uint8_t tps = readTPS() * 10;  // 45.6% → 456, cabe em uint8? NÃO!
    // ATENÇÃO: TPS 0-100% com 0.1% = 0-1000 valores → precisa uint16!
    // Mas no DBC está como 8 bits... Verificar!
    
    // Byte 5-6: Lambda (uint16, 0.001 de resolução)
    uint16_t lambda_scaled = readLambda() * 1000;  // 1.023 → 1023
    data[5] = (lambda_scaled >> 8) & 0xFF;
    data[6] = lambda_scaled & 0xFF;
    
    // Enviar mensagem CAN
    CAN.sendMsgBuf(CAN_ID_MOTOR, 0, 8, data);
}
```

**PROBLEMA DETECTADO**: TPS precisa ser 16 bits para 0.1% de resolução!

---

### Correção: TPS com 16 bits

**Atualizar DBC**:
```dbc
BO_ 256 Motor: 8 Motor
 SG_ RPM : 0|16@1+ (1,0) [0|14000] "rpm" Central
 SG_ Temperatura : 16|16@1+ (0.1,-40) [-40|150] "C" Central
 SG_ TPS : 32|16@1+ (0.1,0) [0|100] "%" Central           # ← Mudou para 16 bits!
 SG_ Lambda : 48|16@1+ (0.001,0) [0.5|1.5] "lambda" Central
```

**Código corrigido**:
```cpp
void sendMotorData() {
    uint8_t data[8];
    
    // Byte 0-1: RPM (uint16, big-endian)
    uint16_t rpm = readRPM();
    data[0] = (rpm >> 8) & 0xFF;
    data[1] = rpm & 0xFF;
    
    // Byte 2-3: Temperatura (uint16, big-endian, 0.1°C, offset -40)
    float temp_real = readTemperatureSensor();  // Ex: 85.2°C
    uint16_t temp_scaled = (uint16_t)((temp_real - (-40.0)) / 0.1);
    data[2] = (temp_scaled >> 8) & 0xFF;
    data[3] = temp_scaled & 0xFF;
    
    // Byte 4-5: TPS (uint16, big-endian, 0.1%)
    float tps_real = readTPSSensor();  // Ex: 45.6%
    uint16_t tps_scaled = (uint16_t)(tps_real / 0.1);  // 45.6 / 0.1 = 456
    data[4] = (tps_scaled >> 8) & 0xFF;
    data[5] = tps_scaled & 0xFF;
    
    // Byte 6-7: Lambda (uint16, big-endian, 0.001)
    float lambda_real = readLambdaSensor();  // Ex: 1.023
    uint16_t lambda_scaled = (uint16_t)(lambda_real / 0.001);  // 1.023 / 0.001 = 1023
    data[6] = (lambda_scaled >> 8) & 0xFF;
    data[7] = lambda_scaled & 0xFF;
    
    CAN.sendMsgBuf(CAN_ID_MOTOR, 0, 8, data);
}
```

---

### Suspensão (4 Sensores, 0.1mm de resolução)

```cpp
/**
 * Envia dados de suspensão via CAN.
 * 
 * DBC: 
 * SG_ SuspensionPos_FL : 0|16@1+ (0.1,0) [0|200] "mm" Central
 * SG_ SuspensionPos_FR : 16|16@1+ (0.1,0) [0|200] "mm" Central
 * SG_ SuspensionPos_RL : 32|16@1+ (0.1,0) [0|200] "mm" Central
 * SG_ SuspensionPos_RR : 48|16@1+ (0.1,0) [0|200] "mm" Central
 */
void sendSuspensionData() {
    uint8_t data[8];
    
    // Ler sensores analógicos (ex: 0-1023 ADC)
    float susp_fl = readSuspensionFL();  // Ex: 45.6 mm
    float susp_fr = readSuspensionFR();  // Ex: 47.2 mm
    float susp_rl = readSuspensionRL();  // Ex: 43.8 mm
    float susp_rr = readSuspensionRR();  // Ex: 44.1 mm
    
    // Escalar para 0.1mm de resolução
    uint16_t fl_scaled = (uint16_t)(susp_fl / 0.1);  // 45.6 / 0.1 = 456
    uint16_t fr_scaled = (uint16_t)(susp_fr / 0.1);  // 47.2 / 0.1 = 472
    uint16_t rl_scaled = (uint16_t)(susp_rl / 0.1);  // 43.8 / 0.1 = 438
    uint16_t rr_scaled = (uint16_t)(susp_rr / 0.1);  // 44.1 / 0.1 = 441
    
    // Byte 0-1: FL
    data[0] = (fl_scaled >> 8) & 0xFF;
    data[1] = fl_scaled & 0xFF;
    
    // Byte 2-3: FR
    data[2] = (fr_scaled >> 8) & 0xFF;
    data[3] = fr_scaled & 0xFF;
    
    // Byte 4-5: RL
    data[4] = (rl_scaled >> 8) & 0xFF;
    data[5] = rl_scaled & 0xFF;
    
    // Byte 6-7: RR
    data[6] = (rr_scaled >> 8) & 0xFF;
    data[7] = rr_scaled & 0xFF;
    
    CAN.sendMsgBuf(CAN_ID_SUSPENSAO, 0, 8, data);
}
```

---

### IMU (Acelerômetro com 0.001G de resolução)

```cpp
/**
 * Envia dados de aceleração via CAN.
 * 
 * DBC:
 * SG_ AccelX : 0|16@1- (0.001,0) [-4|4] "g" Central
 * SG_ AccelY : 16|16@1- (0.001,0) [-4|4] "g" Central
 * 
 * ATENÇÃO: Valores SIGNED (positivo e negativo)!
 */
void sendIMUData() {
    uint8_t data[8];
    
    // Ler acelerômetro (ex: biblioteca Wire/I2C)
    float accel_x = readAccelX();  // Ex: 1.523 G (aceleração)
    float accel_y = readAccelY();  // Ex: -0.234 G (curva esquerda)
    
    // Escalar para 0.001G de resolução
    int16_t accel_x_scaled = (int16_t)(accel_x / 0.001);  // 1.523 / 0.001 = 1523
    int16_t accel_y_scaled = (int16_t)(accel_y / 0.001);  // -0.234 / 0.001 = -234
    
    // Byte 0-1: AccelX (signed int16, big-endian)
    data[0] = (accel_x_scaled >> 8) & 0xFF;
    data[1] = accel_x_scaled & 0xFF;
    
    // Byte 2-3: AccelY (signed int16, big-endian)
    data[2] = (accel_y_scaled >> 8) & 0xFF;
    data[3] = accel_y_scaled & 0xFF;
    
    // Bytes 4-7: Reservado (zeros)
    data[4] = 0;
    data[5] = 0;
    data[6] = 0;
    data[7] = 0;
    
    CAN.sendMsgBuf(CAN_ID_IMU, 0, 8, data);
}
```

---

## 🔄 Loop Principal da ECU

```cpp
void loop() {
    static unsigned long lastMotorSend = 0;
    static unsigned long lastSuspSend = 0;
    static unsigned long lastIMUSend = 0;
    
    unsigned long now = millis();
    
    // Enviar dados do motor a 50 Hz (a cada 20ms)
    if (now - lastMotorSend >= 20) {
        sendMotorData();
        lastMotorSend = now;
    }
    
    // Enviar suspensão a 50 Hz
    if (now - lastSuspSend >= 20) {
        sendSuspensionData();
        lastSuspSend = now;
    }
    
    // Enviar IMU a 50 Hz
    if (now - lastIMUSend >= 20) {
        sendIMUData();
        lastIMUSend = now;
    }
    
    // Outras tarefas...
}
```

---

## 📊 Tabela de Conversão Rápida

### Factor 0.1 (Temperatura, TPS, Suspensão, Freio)

| Valor Real | Cálculo | Valor CAN (uint16) |
|------------|---------|-------------------|
| 0.0 | 0.0 / 0.1 | 0 |
| 10.5 | 10.5 / 0.1 | 105 |
| 45.6 | 45.6 / 0.1 | 456 |
| 85.2 | 85.2 / 0.1 | 852 |
| 200.0 | 200.0 / 0.1 | 2000 |

### Factor 0.001 (Lambda, Aceleração)

| Valor Real | Cálculo | Valor CAN (int16) |
|------------|---------|------------------|
| 0.000 | 0.000 / 0.001 | 0 |
| 1.023 | 1.023 / 0.001 | 1023 |
| 1.500 | 1.500 / 0.001 | 1500 |
| -0.234 | -0.234 / 0.001 | -234 |
| -3.456 | -3.456 / 0.001 | -3456 |

### Com Offset (Temperatura com offset -40)

| Valor Real (°C) | Cálculo | Valor CAN |
|-----------------|---------|-----------|
| -40.0 | (-40 - (-40)) / 0.1 | 0 |
| 0.0 | (0 - (-40)) / 0.1 | 400 |
| 25.0 | (25 - (-40)) / 0.1 | 650 |
| 85.2 | (85.2 - (-40)) / 0.1 | 1252 |
| 150.0 | (150 - (-40)) / 0.1 | 1900 |

---

## ⚠️ Checklist de Validação

Antes de testar no carro:

- [ ] **DBC atualizado** com novos factors
- [ ] **ECU enviando** valores escalados corretamente
- [ ] **Bits suficientes**: uint8 (0-255), uint16 (0-65535), int16 (-32768 a 32767)
- [ ] **Byte order**: Big-endian no exemplo acima (MSB primeiro)
- [ ] **Teste em bancada**: Simular sensor fixo (ex: 85.2°C) e verificar recepção
- [ ] **Validação de range**: Não ultrapassar limites (ex: temperatura > 150°C)
- [ ] **Taxa de envio**: Não saturar barramento CAN (max ~80% de uso)

---

## 🧪 Teste com SavvyCAN

### 1. Conectar adaptador CAN ao computador

### 2. Abrir SavvyCAN e configurar:
- Interface: USB CAN (CH341, SLCAN, etc)
- Bitrate: 500 kbps
- DBC: `pucpr_alta_resolucao.dbc`

### 3. Verificar mensagem Motor (ID 0x100):

**Dados recebidos (hex)**:
```
0D AC 04 E4 01 C8 03 FF
```

**Decodificação manual**:
- Byte 0-1: `0D AC` = 3500 decimal → **RPM = 3500**
- Byte 2-3: `04 E4` = 1252 decimal → **Temp = (1252 × 0.1) + (-40) = 85.2°C** ✅
- Byte 4-5: `01 C8` = 456 decimal → **TPS = 456 × 0.1 = 45.6%** ✅
- Byte 6-7: `03 FF` = 1023 decimal → **Lambda = 1023 × 0.001 = 1.023** ✅

**No SavvyCAN**: Deve mostrar valores decodificados automaticamente.

---

## 🔧 Funções Auxiliares

### Leitura de Sensor Analógico (Suspensão)

```cpp
/**
 * Lê sensor de suspensão analógico (potenciômetro linear).
 * 
 * @param pin Pino analógico (A0-A7)
 * @return Posição em mm (0-200 mm)
 */
float readSuspensionSensor(int pin) {
    int raw = analogRead(pin);  // 0-1023
    
    // Calibração: 0 ADC = 0mm, 1023 ADC = 200mm
    float position_mm = (raw / 1023.0) * 200.0;
    
    return position_mm;
}
```

### Leitura de Acelerômetro I2C (MPU6050)

```cpp
#include <Wire.h>
#include <Adafruit_MPU6050.h>

Adafruit_MPU6050 mpu;

float readAccelX() {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    // Retorna aceleração em G (-4 a +4)
    return a.acceleration.x / 9.81;  // m/s² → G
}

float readAccelY() {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    
    return a.acceleration.y / 9.81;
}
```

---

## 📈 Otimizações Avançadas

### 1. Delta Encoding (Enviar Apenas Mudanças)

```cpp
static uint16_t last_rpm = 0;

void sendRPMDelta() {
    uint16_t current_rpm = readRPM();
    
    // Só envia se mudou mais de 50 RPM
    if (abs((int)current_rpm - (int)last_rpm) > 50) {
        uint8_t data[2];
        data[0] = (current_rpm >> 8) & 0xFF;
        data[1] = current_rpm & 0xFF;
        
        CAN.sendMsgBuf(CAN_ID_MOTOR, 0, 2, data);
        last_rpm = current_rpm;
    }
}
```

**Economia**: Reduz mensagens em ~70% quando RPM estável.

### 2. Compactação de Múltiplos Sensores

**Problema**: 4 rodas × 16 bits = 64 bits (1 mensagem CAN completa)

**Solução**: Reduzir resolução para 8 bits (256 valores) se range for pequeno:

```cpp
// Range: 0-255 km/h com 1 km/h de resolução
uint8_t wheel_fl = (uint8_t)readWheelSpeedFL();
uint8_t wheel_fr = (uint8_t)readWheelSpeedFR();
uint8_t wheel_rl = (uint8_t)readWheelSpeedRL();
uint8_t wheel_rr = (uint8_t)readWheelSpeedRR();

// Cabe em 4 bytes (metade do pacote CAN)
```

**Trade-off**: Menos precisão, mais economia de banda.

---

## 🏁 Conclusão

Para implementar alta resolução:

1. **Atualizar DBC** com novo `Factor`
2. **Modificar firmware da ECU** para enviar valores escalados
3. **Testar em bancada** com SavvyCAN/CANalyzer
4. **Validar no carro** com telemetria real

**Fórmula chave**:
```
Valor CAN = (Valor Real - Offset) / Factor
```

---

**Desenvolvido para PUCPR Racing Formula SAE** 🏎️💨
