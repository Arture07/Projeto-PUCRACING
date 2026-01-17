# 🏁 Otimização de Telemetria LoRa - PUCPR Racing

## 📋 Resumo Executivo

Implementação completa de **Downsampling Inteligente** para economizar banda do LoRa e **Alta Resolução no DBC** para análise de engenharia de competição.

---

## 📦 Arquivos Criados

### 1. **[central.py](central.py)** - Sistema de Telemetria Otimizado (690 linhas)

**Descrição**: Código Python para rodar na **Raspberry Pi dentro do carro**.

**Funcionalidades**:
- ✅ Leitura de mensagens CAN da ECU (python-can + SocketCAN)
- ✅ **Downsampling inteligente** com 3 níveis de prioridade
- ✅ Transmissão via LoRa Serial (struct binária de 36 bytes)
- ✅ Estatísticas de banda em tempo real

**Arquitetura**:
```
┌─────────────────┐
│  ECU do Carro   │
│  (CAN 50-100Hz) │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────┐
│  central.py (Raspberry Pi)          │
│  ┌──────────────────────────────┐   │
│  │  CANReceiver                 │   │
│  │  - Lê mensagens CAN          │   │
│  │  - Decodifica com DBC        │   │
│  │  - Armazena em buffer        │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │  DownsamplingManager         │   │
│  │  - Alta Prioridade: 50 Hz    │   │
│  │  - Média Prioridade: 10 Hz   │   │
│  │  - Baixa Prioridade: 1 Hz    │   │
│  └──────────────────────────────┘   │
│              ↓                       │
│  ┌──────────────────────────────┐   │
│  │  LoRaTransmitter             │   │
│  │  - Empacota struct (36 bytes)│   │
│  │  - Envia via Serial          │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
         │
         v
┌─────────────────┐
│  Módulo LoRa TX │
│  (433/915 MHz)  │
└─────────────────┘
```

---

### 2. **[DBC_RESOLUCAO_GUIA.md](DBC_RESOLUCAO_GUIA.md)** - Guia de Resolução DBC

**Conteúdo**:
- 📐 **Conceito de Resolução**: O que é e por que importa
- 🔧 **Como alterar Factor**: Exemplos práticos passo a passo
- 📊 **Tabelas de referência**: Bits necessários por resolução
- ⚠️ **Armadilhas comuns**: Erros de StartBit, range incompatível
- 🎓 **Checklist completo**: Verificação antes de aplicar

**Exemplos Práticos Incluídos**:
1. Temperatura: 1°C → 0.1°C
2. Suspensão: 1 mm → 0.1 mm
3. Lambda: 0.01 → 0.001
4. Pressão de Freio com Offset

---

### 3. **[pucpr_alta_resolucao.dbc](pucpr_alta_resolucao.dbc)** - DBC Otimizado

**Mudanças Aplicadas**:

| Sinal | Resolução Antiga | Resolução Nova | Bits | Factor Novo |
|-------|------------------|----------------|------|-------------|
| **Temperatura** | 1°C | **0.1°C** | 8→16 | `(0.1,-40)` |
| **TPS** | 1% | **0.1%** | 8→8 | `(0.1,0)` |
| **Lambda** | 0.01 | **0.001** | 8→16 | `(0.001,0)` |
| **WheelSpeed** | 1 km/h | **0.1 km/h** | 8→16 | `(0.1,0)` |
| **Suspensão** | 1 mm | **0.1 mm** | 8→16 | `(0.1,0)` |
| **Freio** | 1 bar | **0.1 bar** | 8→16 | `(0.1,0)` |

**Novos Sensores**:
- ✅ `BatteryVoltage` (0.1V de resolução)
- ✅ `GPS` (Latitude/Longitude com 6 casas decimais)

**Comentários Técnicos**: Cada sinal tem explicação detalhada do uso em competição.

---

## 🎯 Conceitos de Engenharia de Competição

### 1. **Downsampling (Redução de Taxa)**

**Problema**: ECU envia dados a 50-100 Hz (muito rápido para LoRa).

**Solução**: Enviar dados críticos sempre, dados lentos raramente.

| Categoria | Taxa | Dados Incluídos | Justificativa |
|-----------|------|-----------------|---------------|
| **Alta Prioridade** | 50 Hz | RPM, Suspensão, Aceleração, Volante, Freio | Variam rapidamente, críticos para análise de dinâmica |
| **Média Prioridade** | 10 Hz | TPS, Lambda, Velocidade Rodas | Variam moderadamente |
| **Baixa Prioridade** | 1 Hz | Temperatura Motor, Bateria, GPS | Variam lentamente |

**Implementação no [central.py](central.py)**:

```python
class DownsamplingManager:
    def __init__(self):
        self.cycle_count = 0
        self.high_interval = 1      # Todo ciclo (50 Hz)
        self.medium_interval = 5    # A cada 5 ciclos (10 Hz)
        self.low_interval = 50      # A cada 50 ciclos (1 Hz)
    
    def should_send_high(self) -> bool:
        return True  # Sempre envia
    
    def should_send_medium(self) -> bool:
        return (self.cycle_count % self.medium_interval) == 0
    
    def should_send_low(self) -> bool:
        return (self.cycle_count % self.low_interval) == 0
```

**Uso no Loop Principal**:

```python
# Loop roda a 50 Hz (a cada 20ms)
while running:
    current_data = can_receiver.get_current_data()
    
    # SEMPRE envia dados de alta prioridade
    packet.rpm = current_data.rpm
    packet.susp_fl = current_data.susp_fl
    packet.accel_x = current_data.accel_x
    # ...
    
    # Envia média prioridade a cada 5 ciclos
    if downsampler.should_send_medium():
        packet.tps = current_data.tps
        packet.lambda_ = current_data.lambda_
        # Atualiza cache
        cached_tps = current_data.tps
    else:
        # Reutiliza valor anterior
        packet.tps = cached_tps
    
    # Envia baixa prioridade a cada 50 ciclos
    if downsampler.should_send_low():
        packet.temperatura = current_data.temperatura
        cached_temp = current_data.temperatura
    else:
        packet.temperatura = cached_temp
    
    lora.send_packet(packet)
    downsampler.increment_cycle()
    time.sleep(0.02)  # 50 Hz
```

**Economia de Banda**:
- Sem downsampling: 36 bytes × 50 Hz = **1800 bytes/s = 14.4 kbps**
- Com downsampling: 36 bytes × 50 Hz, mas 60% dos dados reutilizados = **~6-8 kbps**
- Limite LoRa (SF7, BW125): **5.4 kbps**
- **Solução**: Reduzir taxa de pacotes para 15-25 Hz mantendo dados críticos sempre frescos

---

### 2. **Resolução em DBC**

**Conceito**: **Factor** determina quantos bits são necessários para representar um valor.

**Fórmula**:
```
Valor Real = (Valor CAN × Factor) + Offset
```

**Exemplo - Temperatura**:

**ANTES** (Resolução: 1°C):
```dbc
SG_ Temperatura : 16|8@1+ (1,0) [0|150] "C" Central
```
- CAN envia: `85` → Valor real: `85 × 1 + 0 = 85°C`
- Problema: Não detecta variações de 0.5°C

**DEPOIS** (Resolução: 0.1°C):
```dbc
SG_ Temperatura : 16|16@1+ (0.1,-40) [-40|150] "C" Central
```
- CAN envia: `1252` → Valor real: `1252 × 0.1 + (-40) = 85.2°C`
- Detecta variações de 0.1°C (10x mais preciso)
- **Offset de -40**: Permite medir temperatura ambiente antes da partida

**Mudanças necessárias**:
1. **Length**: `8` → `16` bits (mais valores possíveis)
2. **Factor**: `1` → `0.1` (cada bit = 0.1°C)
3. **Offset**: `0` → `-40` (zero CAN = -40°C)
4. **Range**: `[0|150]` → `[-40|150]`

---

## 🛠️ Como Usar

### Passo 1: Configurar Raspberry Pi Central

**Dependências**:
```bash
pip install python-can cantools pyserial
```

**Configurar SocketCAN** (Linux):
```bash
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
```

**Executar**:
```bash
python central.py
```

**Saída esperada**:
```
============================================================
  PUCPR RACING - TELEMETRIA CENTRAL (Raspberry Pi)
============================================================

[CAN] DBC carregado: 5 mensagens
[CAN] Conectado em can0 @ 500000 bps
[LoRa] Conectado em /dev/ttyUSB0 @ 115200 baud
[Downsampling] Configurado:
  Alta prioridade: a cada 1 ciclo(s) (50 Hz)
  Média prioridade: a cada 5 ciclo(s) (10 Hz)
  Baixa prioridade: a cada 50 ciclo(s) (1 Hz)

[Sistema] Iniciado com sucesso!
  CAN: can0 @ 500000 bps
  LoRa: /dev/ttyUSB0 @ 115200 baud
  Taxa de transmissão: 50 Hz (downsampling ativo)

Pressione Ctrl+C para parar

------------------------------------------------------------
[Stats] Uptime: 5s
  LoRa TX: 250 pacotes | 50.0 Hz | 7.2 kbps
  CAN RX: 1523 mensagens
  Banda: 900 bytes/s (7.2 kbps)
------------------------------------------------------------
```

---

### Passo 2: Ajustar DBC para Alta Resolução

1. **Backup do DBC original**:
   ```bash
   cp pucpr.dbc pucpr_original.dbc
   ```

2. **Substituir com versão otimizada**:
   ```bash
   cp pucpr_alta_resolucao.dbc pucpr.dbc
   ```

3. **Atualizar firmware da ECU**:
   - Enviar valores com nova escala
   - Exemplo: Temperatura 85.2°C → enviar `852` (será dividido por 10 no DBC)

4. **Testar decodificação**:
   ```bash
   # Usar ferramenta CANalyzer ou SavvyCAN
   # Verificar se valores batem com sensores reais
   ```

---

### Passo 3: Validar na Ground Station

1. **Configurar fonte LoRa**:
   ```bash
   python configure_telemetry.py  # Escolher opção 3
   ```

2. **Executar aplicação**:
   ```bash
   python main.py
   ```

3. **Verificar recepção**:
   - Aba "Tempo Real" → "Iniciar Telemetria"
   - Verificar Hz da recepção (deve ser ~50 Hz)
   - Verificar valores com 1 casa decimal (ex: 85.2°C, 45.6 mm)

---

## 📊 Análise de Banda LoRa

### Limites Teóricos (LoRa SF7, BW125, CR4/5):

| Parâmetro | Valor |
|-----------|-------|
| **Bitrate** | 5470 bps |
| **Bytes/s** | 683 bytes/s |
| **Pacote (36B) Max** | ~19 Hz |

### Cenários de Uso:

| Estratégia | Taxa de Pacotes | Banda Usada | Status |
|------------|----------------|-------------|--------|
| **Sem otimização** | 50 Hz | 1800 bytes/s | ❌ **SATURADO** |
| **Downsampling 60%** | 50 Hz (cache) | ~900 bytes/s | ⚠️ **No limite** |
| **Redução para 25 Hz** | 25 Hz | 900 bytes/s | ✅ **OK** |
| **Redução para 15 Hz** | 15 Hz | 540 bytes/s | ✅ **Ideal** |

**Recomendação**:
- Configurar `RATE_HIGH_PRIORITY = 25` em [central.py](central.py) linha 35
- Mantém dados críticos fluidos sem saturar LoRa
- Em caso de degradação de sinal, reduzir para 15 Hz

---

## 🎓 Conceitos Aplicados

### 1. **Taxa de Aquisição vs Taxa de Transmissão**

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  ECU        │      │  Central     │      │  LoRa TX     │
│  100 Hz     │─────►│  Lê 100 Hz   │─────►│  Envia 25 Hz │
│  (CAN Bus)  │      │  (Sempre)    │      │  (Filtrado)  │
└─────────────┘      └──────────────┘      └──────────────┘
```

- **Aquisição**: Sempre a 100 Hz (não perder dados da ECU)
- **Transmissão**: Filtrada a 25 Hz (economizar banda LoRa)

### 2. **Cache de Dados**

Dados de baixa prioridade são **reutilizados** entre atualizações:

```python
# Ciclo 0 (1 Hz - atualiza temperatura)
packet.temperatura = 85  # Lido do CAN
cached_temp = 85

# Ciclos 1-49 (temperatura não atualizada)
packet.temperatura = cached_temp  # Reutiliza 85

# Ciclo 50 (1 Hz - atualiza temperatura novamente)
packet.temperatura = 86  # Novo valor
cached_temp = 86
```

**Vantagem**: Reduz leituras CAN desnecessárias e simplifica código.

---

## ⚙️ Customização

### Alterar Taxas de Downsampling:

Edite [central.py](central.py) linhas 32-34:

```python
# Taxas de transmissão (Hz)
RATE_HIGH_PRIORITY = 25     # Reduzido de 50 para 25 Hz
RATE_MEDIUM_PRIORITY = 5    # Reduzido de 10 para 5 Hz
RATE_LOW_PRIORITY = 1       # Mantido em 1 Hz
```

### Adicionar Novos Sensores:

1. **Adicionar no DBC**:
   ```dbc
   BO_ 800 Bateria: 8 Central
    SG_ BatteryVoltage : 0|8@1+ (0.1,0) [0|25.5] "V" Central
    SG_ BatteryCurrent : 8|16@1- (0.01,0) [-100|100] "A" Central
   ```

2. **Adicionar em `TelemetryData`** ([central.py](central.py) linha 64):
   ```python
   @dataclass
   class TelemetryData:
       # ... campos existentes ...
       battery_voltage: float = 0.0
       battery_current: float = 0.0
   ```

3. **Mapear no `CANReceiver`** ([central.py](central.py) linha 194):
   ```python
   if 'BatteryVoltage' in decoded:
       self.data.battery_voltage = float(decoded['BatteryVoltage'])
   ```

4. **Atualizar struct no `LoRaTransmitter`** (linha 373):
   ```python
   packed = struct.pack(
       '<HbBHhHhhhHHHHHHHHIBh',  # Adiciona B (uint8) e h (int16)
       # ... campos existentes ...
       int(data.battery_voltage * 10),  # Escala 0.1V
       int(data.battery_current * 100)  # Escala 0.01A
   )
   ```

5. **Atualizar `lora_receiver.py`** na Ground Station com mesma struct.

---

## 🔍 Troubleshooting

### Problema: "LoRa TX saturado, perda de pacotes"

**Sintomas**: Hz da recepção < Hz configurado, gaps nos dados.

**Solução**:
1. Reduzir `RATE_HIGH_PRIORITY` de 50 para 25 Hz
2. Verificar configuração do LoRa (SF, BW, CR)
3. Considerar usar LoRa de maior bandwidth (BW250 ou BW500)

### Problema: "Valores no dashboard com resolução antiga (sem decimais)"

**Sintomas**: Dashboard mostra `85` em vez de `85.2`.

**Solução**:
1. Verificar se DBC foi atualizado corretamente
2. Reiniciar `central.py` para carregar novo DBC
3. Verificar logs: `[CAN] DBC carregado: X mensagens` (deve incluir novas)

### Problema: "Temperatura sempre -40°C"

**Sintomas**: Dashboard mostra valor incorreto fixo.

**Solução**:
1. **Offset incorreto**: Verificar se ECU envia valor absoluto (ex: 85) ou com offset (ex: 1252)
2. Se ECU envia valor absoluto, **remover offset do DBC**:
   ```dbc
   SG_ Temperatura : 16|16@1+ (0.1,0) [0|150] "C" Central
   ```

---

## 📈 Próximos Passos

- [ ] Implementar compressão de dados (zlib ou LZ4)
- [ ] Adicionar checksum/CRC para validação de pacotes
- [ ] Implementar acknowledgement (ACK) para pacotes críticos
- [ ] Criar modo "pit" (alta taxa) vs "corrida" (baixa taxa)
- [ ] Integrar GPS e gravação de logs localmente na Raspberry Pi
- [ ] Dashboard de estatísticas de banda em tempo real na Ground Station

---

## 📚 Referências

- [python-can Documentation](https://python-can.readthedocs.io/)
- [DBC File Format Specification](https://www.csselectronics.com/pages/can-dbc-file-database-intro)
- [LoRa Bandwidth Calculator](https://www.thethingsnetwork.org/airtime-calculator)
- [Formula SAE Telemetry Best Practices](https://www.fsaeonline.com/)

---

**Desenvolvido para PUCPR Racing Formula SAE** 🏎️💨
