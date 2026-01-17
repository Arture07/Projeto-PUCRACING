# 📐 Guia de Resolução em Arquivos DBC - PUCPR Racing

## 🎯 O que é Resolução?

**Resolução** é a menor variação que um sensor pode medir. Em engenharia de competição, alta resolução permite detectar mudanças sutis que podem indicar problemas ou oportunidades de otimização.

### Exemplos Práticos:

| Sensor | Resolução Baixa | Resolução Alta | Impacto |
|--------|----------------|----------------|---------|
| **Temperatura** | 1°C | 0.1°C | Detectar aquecimento gradual antes de crítico |
| **Suspensão** | 1 mm | 0.1 mm | Análise precisa de bumps e curvas |
| **Lambda** | 0.01 | 0.001 | Ajuste fino de mistura ar/combustível |
| **Pressão Freio** | 1 bar | 0.1 bar | Telemetria de modulação do piloto |

## 📄 Anatomia de uma Linha DBC

### Formato Completo:

```
SG_ NomeSinal : StartBit|Length@ByteOrder Signed (Factor,Offset) [Min|Max] "Unit" Receiver
```

### Exemplo Real (Temperatura do Motor):

```dbc
SG_ EngineTemp : 0|8@1+ (1,0) [0|150] "°C" Central
```

**Decodificação**:
- `SG_`: Signal (Sinal)
- `EngineTemp`: Nome do sinal
- `0|8`: Começa no bit 0, usa 8 bits (1 byte)
- `@1+`: Big-endian, unsigned (sem sinal)
- `(1,0)`: **Factor=1, Offset=0**
- `[0|150]`: Range de 0 a 150°C
- `"°C"`: Unidade
- `Central`: Receptor

### Fórmula de Conversão:

```
Valor Real = (Valor CAN × Factor) + Offset
```

## 🔧 Como Alterar a Resolução

### Cenário 1: Temperatura com Resolução de 0.1°C

**ANTES** (resolução de 1°C):
```dbc
SG_ EngineTemp : 0|8@1+ (1,0) [0|150] "°C" Central
```
- Range: 0-255 valores (8 bits unsigned)
- Resolução: 1°C por step
- Exemplo CAN: 85 → 85°C

**DEPOIS** (resolução de 0.1°C):
```dbc
SG_ EngineTemp : 0|16@1+ (0.1,0) [0|400] "°C" Central
```
- Range: 0-65535 valores (16 bits unsigned)
- Resolução: 0.1°C por step
- **Factor alterado: 1 → 0.1**
- **Length alterado: 8 → 16 bits**
- Exemplo CAN: 852 → 85.2°C

**Mudanças**:
1. `8` → `16` (aumenta bits para mais precisão)
2. `(1,0)` → `(0.1,0)` (cada bit = 0.1°C)
3. `[0|150]` → `[0|400]` (novo range: 400/0.1 = 4000 valores)

---

### Cenário 2: Suspensão com Resolução de 0.1 mm

**ANTES** (resolução de 1 mm):
```dbc
SG_ Suspension_FL : 0|8@1+ (1,0) [0|200] "mm" Central
```
- Range: 0-255 valores
- Resolução: 1 mm
- Exemplo CAN: 45 → 45 mm

**DEPOIS** (resolução de 0.1 mm):
```dbc
SG_ Suspension_FL : 0|16@1+ (0.1,0) [0|200] "mm" Central
```
- Range: 0-65535 valores
- Resolução: 0.1 mm
- **Factor: 1 → 0.1**
- **Length: 8 → 16 bits**
- Exemplo CAN: 456 → 45.6 mm

**Por que importa?**
- Detecta variações sutis na geometria da suspensão
- Permite análise detalhada de ride height em curvas
- Correlaciona com dados de aceleração lateral para setup

---

### Cenário 3: Lambda (AFR) com Resolução de 0.001

**ANTES** (resolução de 0.01):
```dbc
SG_ Lambda : 0|8@1+ (0.01,0) [0.5|1.5] "" Central
```
- Range: 0-255 valores
- Resolução: 0.01 (1%)
- Exemplo CAN: 100 → 1.00

**DEPOIS** (resolução de 0.001):
```dbc
SG_ Lambda : 0|16@1+ (0.001,0) [0.5|1.5] "" Central
```
- Range: 0-65535 valores
- Resolução: 0.001 (0.1%)
- **Factor: 0.01 → 0.001**
- **Length: 8 → 16 bits**
- Exemplo CAN: 1023 → 1.023

**Impacto na Competição**:
- Ajuste preciso de mistura para máxima potência
- Detecta vazamentos ou problemas no sistema de injeção
- Evita mistura pobre (risco de detonação) ou rica (perda de potência)

---

### Cenário 4: Pressão de Freio com Offset

**ANTES** (range 0-200 bar):
```dbc
SG_ BrakePressure : 0|8@1+ (1,0) [0|200] "bar" Central
```

**DEPOIS** (range -10 a 200 bar, detecta vácuo):
```dbc
SG_ BrakePressure : 0|8@1- (1,-10) [-10|200] "bar" Central
```
- **Signed alterado: `+` → `-`** (permite valores negativos)
- **Offset alterado: 0 → -10**
- Exemplo CAN: 5 → (5 × 1) + (-10) = -5 bar (vácuo residual)

**Quando usar offset?**
- Sensores que têm valor "zero" diferente de 0 CAN
- Exemplo: Sensor de temperatura que mede de -40°C a 125°C
  - Offset = -40
  - CAN 0 → -40°C | CAN 165 → 125°C

---

## 📊 Tabela de Referência Rápida

| Factor | Resolução | Bits Necessários | Range (16 bits) | Uso Típico |
|--------|-----------|------------------|-----------------|------------|
| **1** | 1 unidade | 8-16 | 0-65535 | RPM, Velocidade |
| **0.1** | 0.1 unidade | 16 | 0-6553.5 | Temperatura, Pressão |
| **0.01** | 0.01 unidade | 16 | 0-655.35 | Lambda, Throttle (%) |
| **0.001** | 0.001 unidade | 16 | 0-65.535 | AFR preciso, Sensores de precisão |
| **10** | 10 unidades | 8 | 0-2550 | RPM compactado (0-25500) |

---

## 🛠️ Exemplo Prático Completo: Modificar pucpr.dbc

### Arquivo Original (Baixa Resolução):

```dbc
VERSION ""

NS_ :
    NS_CM_
    NS_DESC_
    BA_DEF_
    BA_
    VAL_

BS_:

BU_: Central Motor Suspensao

BO_ 256 Motor_Data: 8 Motor
 SG_ RPM : 0|16@1+ (1,0) [0|13000] "rpm" Central
 SG_ EngineTemp : 16|8@1+ (1,0) [0|150] "°C" Central
 SG_ TPS : 24|8@1+ (1,0) [0|100] "%" Central
 SG_ Lambda : 32|8@1+ (0.01,0) [0.5|1.5] "" Central

BO_ 512 Suspension_Data: 8 Suspensao
 SG_ Suspension_FL : 0|8@1+ (1,0) [0|200] "mm" Central
 SG_ Suspension_FR : 8|8@1+ (1,0) [0|200] "mm" Central
 SG_ Suspension_RL : 16|8@1+ (1,0) [0|200] "mm" Central
 SG_ Suspension_RR : 24|8@1+ (1,0) [0|200] "mm" Central
```

### Arquivo Modificado (Alta Resolução):

```dbc
VERSION ""

NS_ :
    NS_CM_
    NS_DESC_
    BA_DEF_
    BA_
    VAL_

BS_:

BU_: Central Motor Suspensao

BO_ 256 Motor_Data: 8 Motor
 SG_ RPM : 0|16@1+ (1,0) [0|13000] "rpm" Central
 SG_ EngineTemp : 16|16@1+ (0.1,0) [0|150] "°C" Central          # ✓ Mudou para 0.1°C
 SG_ TPS : 32|8@1+ (0.1,0) [0|100] "%" Central                  # ✓ Mudou para 0.1%
 SG_ Lambda : 40|16@1+ (0.001,0) [0.5|1.5] "" Central           # ✓ Mudou para 0.001

BO_ 512 Suspension_Data: 8 Suspensao
 SG_ Suspension_FL : 0|16@1+ (0.1,0) [0|200] "mm" Central       # ✓ Mudou para 0.1mm
 SG_ Suspension_FR : 16|16@1+ (0.1,0) [0|200] "mm" Central      # ✓ Mudou para 0.1mm
 SG_ Suspension_RL : 32|16@1+ (0.1,0) [0|200] "mm" Central      # ✓ Mudou para 0.1mm
 SG_ Suspension_RR : 48|16@1+ (0.1,0) [0|200] "mm" Central      # ✓ Mudou para 0.1mm
```

**IMPORTANTE**: Ao mudar para 16 bits, o StartBit também muda!
- Temperatura: `16|8` → `16|16`
- TPS: `24|8` → `32|8` (ajusta posição)
- Lambda: `32|8` → `40|16`

---

## ⚠️ Armadilhas Comuns

### 1. Esquecer de Ajustar StartBit
```dbc
# ❌ ERRADO (bits vão se sobrepor)
SG_ EngineTemp : 16|16@1+ (0.1,0) [0|150] "°C" Central
SG_ TPS : 24|8@1+ (1,0) [0|100] "%" Central  # Começa antes do anterior terminar!

# ✓ CORRETO
SG_ EngineTemp : 16|16@1+ (0.1,0) [0|150] "°C" Central
SG_ TPS : 32|8@1+ (1,0) [0|100] "%" Central  # Ajusta para começar após 16+16=32
```

### 2. Range Incompatível com Bits
```dbc
# ❌ ERRADO (150/0.1 = 1500 valores, cabe em 11 bits, mas declarou 8)
SG_ EngineTemp : 0|8@1+ (0.1,0) [0|150] "°C" Central  # Max 255 valores!

# ✓ CORRETO
SG_ EngineTemp : 0|16@1+ (0.1,0) [0|150] "°C" Central  # 16 bits = 65535 valores
```

### 3. Não Atualizar Código da ECU
- DBC é apenas definição para **decodificação**
- ECU precisa **enviar** dados com a nova escala
- Exemplo: Se mudou temperatura para 0.1°C, ECU deve enviar `852` (85.2°C), não `85`

---

## 🎓 Checklist de Alteração de Resolução

- [ ] Identificar sensor que precisa maior precisão
- [ ] Calcular novo factor (ex: 1 → 0.1 para 10x mais precisão)
- [ ] Calcular bits necessários: `log2(Range/Factor)`
- [ ] Atualizar `Length` na linha `SG_`
- [ ] Atualizar `Factor` em `(Factor,Offset)`
- [ ] Ajustar `StartBit` dos sinais seguintes (se necessário)
- [ ] Verificar que mensagem CAN não ultrapassa 8 bytes (64 bits)
- [ ] Atualizar firmware da ECU para enviar com nova escala
- [ ] Testar com ferramenta CAN (CANalyzer, SavvyCAN)
- [ ] Validar decodificação no `central.py` e `lora_receiver.py`

---

## 📈 Impacto no Tamanho do Pacote CAN

### Exemplo: Motor_Data

**Configuração Baixa Resolução** (8+8+8+8 = 32 bits = 4 bytes):
```dbc
BO_ 256 Motor_Data: 8 Motor
 SG_ RPM : 0|16@1+ (1,0) [0|13000] "rpm" Central
 SG_ EngineTemp : 16|8@1+ (1,0) [0|150] "°C" Central
 SG_ TPS : 24|8@1+ (1,0) [0|100] "%" Central
 SG_ Lambda : 32|8@1+ (0.01,0) [0.5|1.5] "" Central
```
- **Total: 40 bits (5 bytes)** → Cabe tranquilamente em 1 mensagem CAN (max 8 bytes)

**Configuração Alta Resolução** (16+16+16+16 = 64 bits = 8 bytes):
```dbc
BO_ 256 Motor_Data: 8 Motor
 SG_ RPM : 0|16@1+ (1,0) [0|13000] "rpm" Central
 SG_ EngineTemp : 16|16@1+ (0.1,0) [0|150] "°C" Central
 SG_ TPS : 32|16@1+ (0.01,0) [0|100] "%" Central
 SG_ Lambda : 48|16@1+ (0.001,0) [0.5|1.5] "" Central
```
- **Total: 64 bits (8 bytes)** → **Máximo de 1 mensagem CAN!**

**Lição**: Se precisar adicionar mais sensores, terá que criar nova mensagem CAN (ex: `BO_ 257`).

---

## 🏁 Conclusão

A **resolução no DBC** é ajustada pelo **Factor**:
- Factor maior (ex: 10) = **compressão** (menos precisão, menos bytes)
- Factor menor (ex: 0.1, 0.01) = **expansão** (mais precisão, mais bytes)

Para engenharia de competição:
- **Dados críticos** (RPM, Suspensão, Lambda): Alta resolução (0.1, 0.01, 0.001)
- **Dados lentos** (Temperatura, GPS): Resolução média (0.1, 1)
- **Otimizar banda LoRa**: Usar downsampling em `central.py` (enviar a 1-10 Hz)

---

**Desenvolvido para PUCPR Racing Formula SAE** 🏎️💨
