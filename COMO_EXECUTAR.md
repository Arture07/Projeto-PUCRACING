# 🚀 Como Executar o Projeto PUCPR Racing

## 📋 Visão Geral

O projeto tem **dois componentes**:

1. **Ground Station** (PC Windows/Linux) - Recebe e visualiza dados
2. **Central** (Raspberry Pi no carro) - Captura e transmite dados via LoRa

---

## 💻 GROUND STATION (Seu Computador)

### Opção 1: Receber Telemetria Real (LoRa ou CAN)

#### Passo 1: Escolher Fonte de Dados

```bash
python configure_telemetry.py
```

**Menu**:
```
[1] CAN Bus (UDP Multicast) - Windows/Rede
[2] CAN Bus (SocketCAN) - Linux direto
[3] LoRa (Serial USB) - Receptor LoRa conectado
[4] Simulador CAN - Testes sem hardware
```

Escolha **3** se tiver receptor LoRa, ou **4** para testar sem hardware.

---

#### Passo 2: Executar Aplicação Principal

```bash
python main.py
```

**O que acontece**:
- Abre interface gráfica (CustomTkinter)
- 5 abas disponíveis:
  - **📊 Análise de Logs** - Carregar CSV e visualizar
  - **📡 Tempo Real** - Telemetria ao vivo
  - **⚙️ Configurações** - Ajustes gerais
  - **📈 Gráficos Comparativos** - Comparar múltiplas voltas
  - **🔧 Ferramentas** - Utilidades extras

---

#### Passo 3: Iniciar Telemetria em Tempo Real

1. Clique na aba **"Tempo Real"**
2. Clique no botão **"▶️ Iniciar Telemetria"**
3. Dashboard será atualizado automaticamente

**Se escolheu LoRa (opção 3)**:
- Conecte receptor LoRa USB
- Sistema detecta porta automaticamente (COM3, /dev/ttyUSB0, etc)
- Status mostra: `"LoRa X.X Hz"` com taxa de recepção

**Se escolheu Simulador (opção 4)**:
- Precisa rodar simulador em terminal separado (veja abaixo)

---

### Opção 2: Simular Dados (Sem Hardware)

#### Terminal 1 - Simulador:
```bash
python simulador_carro.py
```

**Saída esperada**:
```
[Simulador] Enviando dados CAN via UDP Multicast...
RPM: 3500 | Temp: 85°C | TPS: 45%
```

#### Terminal 2 - Aplicação:
```bash
python configure_telemetry.py  # Escolher opção 4 (Simulador)
python main.py
```

---

## 🏎️ CENTRAL (Raspberry Pi no Carro)

### Pré-requisitos:

```bash
# Instalar dependências
sudo apt update
sudo apt install python3-pip can-utils

pip3 install python-can cantools pyserial
```

---

### Configurar Interface CAN (SocketCAN):

```bash
# Configurar CAN0 a 500 kbps
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up

# Verificar se está ativo
ifconfig can0
```

**Saída esperada**:
```
can0: flags=193<UP,RUNNING,NOARP>  mtu 16
```

---

### Conectar Módulo LoRa:

1. **Conectar LoRa TX na porta USB**:
   ```bash
   ls /dev/ttyUSB*  # Deve mostrar /dev/ttyUSB0
   ```

2. **Verificar permissões**:
   ```bash
   sudo usermod -a -G dialout $USER
   sudo chmod 666 /dev/ttyUSB0
   ```

---

### Executar Central:

```bash
python3 central.py
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

## 🔄 Fluxo Completo (Carro → Ground Station)

```
┌─────────────────────┐
│   ECU do Carro      │
│   (CAN Bus)         │
└──────────┬──────────┘
           │ 100 Hz
           ▼
┌─────────────────────┐
│ Raspberry Pi        │
│ central.py          │
│ - Lê CAN           │
│ - Downsampling     │
│ - Empacota (36B)   │
└──────────┬──────────┘
           │ LoRa TX
           │ 50 Hz
           ▼
    ╔══════════════╗
    ║  LoRa Radio  ║
    ║  433/915 MHz ║
    ╚══════════════╝
           │ Sem Fios
           │ até 2-15 km
           ▼
    ╔══════════════╗
    ║  LoRa Radio  ║
    ║  RX (USB)    ║
    ╚══════════════╝
           │ Serial
           ▼
┌─────────────────────┐
│ PC Ground Station   │
│ main.py             │
│ - Recebe Serial    │
│ - Desempacota      │
│ - Atualiza GUI     │
└─────────────────────┘
```

---

## 🧪 Teste Rápido (Sem Hardware Completo)

### Cenário 1: Testar Ground Station Isolada

```bash
# Terminal 1: Simulador
python simulador_carro.py

# Terminal 2: Aplicação
python configure_telemetry.py  # Opção 4
python main.py
```

---

### Cenário 2: Testar Receptor LoRa (Sem Central)

```bash
# Testar apenas recepção LoRa
python -m core.lora_receiver
```

**Saída se nenhum dado chegar**:
```
=== Teste do Receptor LoRa ===
[LoRa] Porto detectado: COM3
[LoRa] Conectado em COM3 @ 115200 baud
Recebendo dados... (Ctrl+C para parar)

(sem output - aguardando pacotes)
```

---

### Cenário 3: Testar Central (Sem ECU Real)

```bash
# Na Raspberry Pi, criar simulador CAN local
cangen can0 -v -g 10  # Gera mensagens aleatórias a cada 10ms

# Em outro terminal
python3 central.py
```

---

## ⚙️ Configurações Importantes

### Ajustar Taxa de Transmissão LoRa:

Edite **central.py** linha 35:
```python
RATE_HIGH_PRIORITY = 25  # Reduzir de 50 para 25 Hz (economizar banda)
```

---

### Trocar Porta Serial do LoRa:

Edite **central.py** linha 38:
```python
LORA_PORT = '/dev/ttyUSB0'  # Ou '/dev/ttyAMA0', 'COM3', etc
```

---

### Usar DBC Customizado:

Edite **central.py** linha 36:
```python
DBC_FILE = 'pucpr_alta_resolucao.dbc'  # Seu arquivo DBC
```

---

## 📊 Carregar e Analisar Logs

### Passo 1: Executar Aplicação
```bash
python main.py
```

### Passo 2: Aba "Análise de Logs"
1. Clique em **"Carregar Log CSV"**
2. Selecione arquivo (ex: `exemplo_log_pucpr_realista.csv`)
3. Escolha eixo X (Tempo, Distância, etc)
4. Escolha variáveis para plotar
5. Clique **"Plotar"**

### Passo 3: Análises Disponíveis
- **G-G Diagram** - Aceleração lateral vs longitudinal
- **Suspensão vs Tempo** - Movimento das 4 rodas
- **Comparar Voltas** - Múltiplos arquivos CSV

---

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'cantools'"

**Solução**:
```bash
pip install python-can cantools pyserial
```

---

### Problema: "Permission denied: '/dev/ttyUSB0'"

**Solução**:
```bash
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
# Fazer logout e login novamente
```

---

### Problema: "CAN interface 'can0' not found"

**Solução**:
```bash
# Verificar interfaces CAN
ip link show

# Configurar CAN0
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
```

---

### Problema: "Nenhum dado recebido no dashboard"

**Checklist**:
- [ ] Configurou fonte correta? (`python configure_telemetry.py`)
- [ ] Simulador rodando? (se opção 4)
- [ ] Receptor LoRa conectado? (se opção 3)
- [ ] Clicou em "Iniciar Telemetria"?
- [ ] Status mostra Hz? (ex: "LoRa 25.3 Hz")

---

### Problema: "LoRa conectado mas Hz = 0"

**Possíveis causas**:
1. **Central não está transmitindo** - Verificar central.py rodando
2. **Frequência LoRa diferente** - TX e RX devem estar na mesma frequência
3. **Distância muito grande** - Testar com módulos próximos
4. **Porta serial errada** - Verificar em Gerenciador de Dispositivos (Windows)

---

## 📁 Estrutura de Arquivos

```
Projeto PUCRACING/
│
├── main.py                    # ← EXECUTAR (Ground Station)
├── main_gui.py               # (mesmo que main.py)
├── central.py                # ← EXECUTAR (Raspberry Pi)
├── configure_telemetry.py    # Configurador de fonte
├── simulador_carro.py        # Simulador de dados
│
├── pucpr.dbc                 # Definições CAN (original)
├── pucpr_alta_resolucao.dbc  # Definições CAN (otimizado)
│
├── core/
│   ├── lora_receiver.py      # Receptor LoRa (Ground Station)
│   ├── telemetry_realtime.py # Telemetria CAN (Ground Station)
│   ├── constants.py
│   └── analysis_callbacks.py
│
├── gui/
│   ├── dashboards.py
│   └── live_plotting.py
│
└── docs/
    ├── LORA_SETUP.md
    ├── OTIMIZACAO_LORA.md
    ├── DBC_RESOLUCAO_GUIA.md
    └── ECU_EXEMPLO_CODIGO.md
```

---

## 🎯 Casos de Uso Comuns

### 1. **Análise de Log Offline**
```bash
python main.py
# → Aba "Análise de Logs" → Carregar CSV
```

### 2. **Telemetria em Tempo Real (Pit/Oficina com Simulador)**
```bash
# Terminal 1
python simulador_carro.py

# Terminal 2
python configure_telemetry.py  # Opção 4
python main.py  # → Aba "Tempo Real" → Iniciar
```

### 3. **Telemetria em Tempo Real (Corrida com LoRa)**
```bash
# No carro (Raspberry Pi)
python3 central.py

# No pit (PC)
python configure_telemetry.py  # Opção 3
python main.py  # → Aba "Tempo Real" → Iniciar
```

### 4. **Desenvolvimento/Debug de Código**
```bash
# Testar apenas receptor LoRa
python -m core.lora_receiver

# Testar apenas simulador CAN
python simulador_carro.py
```

---

## 📚 Documentação Adicional

- **[LORA_SETUP.md](LORA_SETUP.md)** - Setup detalhado do sistema LoRa
- **[OTIMIZACAO_LORA.md](OTIMIZACAO_LORA.md)** - Downsampling e otimização
- **[DBC_RESOLUCAO_GUIA.md](DBC_RESOLUCAO_GUIA.md)** - Como alterar resolução no DBC
- **[ECU_EXEMPLO_CODIGO.md](ECU_EXEMPLO_CODIGO.md)** - Código Arduino para ECU

---

## 🚀 Início Rápido (TL;DR)

### Ground Station (PC):
```bash
pip install customtkinter matplotlib cantools pyserial python-can
python configure_telemetry.py  # Opção 4 (Simulador)
python simulador_carro.py      # Terminal separado
python main.py                 # Aba "Tempo Real" → Iniciar
```

### Central (Raspberry Pi):
```bash
sudo ip link set can0 type can bitrate 500000 && sudo ip link set can0 up
pip3 install python-can cantools pyserial
python3 central.py
```

---

**Desenvolvido para PUCPR Racing Formula SAE** 🏎️💨
