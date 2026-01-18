# 🏎️ PUCPR Racing - Sistema de Telemetria

Sistema completo de telemetria para Formula SAE desenvolvido pela equipe PUCPR Racing.

## 🎯 Funcionalidades

### Ground Station (PC)
- 📊 **Análise Offline**: Carregar e analisar logs CSV
- 📡 **Telemetria em Tempo Real**: CAN Bus (UDP/SocketCAN) ou LoRa Serial
- 📈 **Visualizações**: G-G Diagram, GPS Track, Suspensão, Voltas
- 🔧 **Configurável**: Mapeamento flexível de canais via config.ini

### Central (Raspberry Pi)
- 🚗 **Aquisição CAN**: Lê dados da ECU a 50-100 Hz
- 📡 **Transmissão LoRa**: Downsampling inteligente (otimização de banda)
- 💾 **Data Logging**: Gravação local em CSV (backup completo)
- ⚡ **Tempo Real**: Sistema de alta performance com threading

---

## 🚀 Início Rápido

### Ground Station (Análise e Visualização)

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar fonte de dados
python configure_telemetry.py
# Opções:
#   [1] CAN Bus UDP (Windows)
#   [2] CAN Bus SocketCAN (Linux)
#   [3] LoRa Serial (Receptor USB)
#   [4] Simulador (Testes)

# Executar aplicação
python main.py
```

**Modo teste** (sem hardware):
```bash
# Terminal 1: Simulador
python simulador_carro.py

# Terminal 2: Aplicação
python configure_telemetry.py  # Escolher opção 4
python main.py
```

### Central (Raspberry Pi no Carro)

```bash
# Configurar CAN
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up

# Executar central
python3 central.py
```

---

## 📖 Documentação

| Guia | Descrição |
|------|-----------|
| **[COMO_EXECUTAR.md](COMO_EXECUTAR.md)** | Guia completo de execução da Ground Station |
| **[GUIA_CENTRAL.md](GUIA_CENTRAL.md)** | Guia da Central (Raspberry Pi) |

---

## 📁 Estrutura do Projeto

```
Projeto PUCRACING/
│
├── main.py                    # Ponto de entrada (Ground Station)
├── main_gui.py               # Interface gráfica principal
├── central.py                # Sistema central (Raspberry Pi)
├── configure_telemetry.py    # Configurador de fonte de dados
├── simulador_carro.py        # Simulador de dados CAN
│
├── pucpr.dbc                 # Definições CAN Bus
├── config_pucpr_tool.ini     # Configuração de canais
├── requirements.txt          # Dependências Python
│
├── core/                     # Módulos principais
│   ├── lora_receiver.py      # Receptor LoRa (Ground Station)
│   ├── telemetry_realtime.py # Telemetria CAN
│   ├── constants.py
│   └── analysis_callbacks.py
│
├── gui/                      # Interface gráfica
│   ├── dashboards.py
│   └── live_plotting.py
│
└── logs/                     # Logs CSV (gerados automaticamente)
    └── telemetria_pucpr_*.csv
```

---

## 🔧 Requisitos

### Ground Station
- Python 3.8+
- Windows 10/11 ou Linux
- Dependências: `pip install -r requirements.txt`

### Central (Raspberry Pi)
- Raspberry Pi 3/4 com Raspbian/Ubuntu
- Interface CAN (MCP2515 ou similar)
- Módulo LoRa Serial
- Python 3.8+
- Pacotes: `python-can`, `cantools`, `pyserial`

---

## 🎓 Conceitos Aplicados

### Downsampling (Otimização de Banda LoRa)

```
ECU → CAN 100Hz → Central (Raspberry Pi)
                      ├─→ LoRa TX (Downsampling)
                      │   - Alta prioridade: 50 Hz (RPM, Suspensão)
                      │   - Média prioridade: 10 Hz (TPS, Lambda)
                      │   - Baixa prioridade: 1 Hz (Temperatura)
                      │
                      └─→ CSV Log (Completo)
                          - TUDO a 100 Hz (backup local)
```

**Economia**: 14.4 kbps → 7.2 kbps (50% de redução sem perder dados críticos)

---

## 📊 Exemplo de Uso

### 1. Análise Offline (Logs CSV)
```python
# Executar main.py
# → Aba "Análise de Logs"
# → Carregar exemplo_log_pucpr_realista.csv
# → Selecionar canais (RPM, WheelSpeed_FL, etc)
# → Plotar
```

### 2. Telemetria em Tempo Real
```python
# Executar main.py
# → Aba "Tempo Real"
# → Clicar "Iniciar Telemetria"
# → Dashboard atualiza automaticamente
```

### 3. Central no Carro (Corrida)
```bash
# Na Raspberry Pi
python3 central.py

# Logs salvos em:
./logs/telemetria_pucpr_20260117_143025.csv
```

---

## 🐛 Troubleshooting

### Ground Station

**Problema**: `ModuleNotFoundError`
```bash
pip install -r requirements.txt
```

**Problema**: "Nenhum dado recebido"
- Verificar se simulador está rodando (ou hardware conectado)
- Verificar configuração em `configure_telemetry.py`
- Clicar "Iniciar Telemetria" na aba Tempo Real

### Central (Raspberry Pi)

**Problema**: "CAN interface 'can0' not found"
```bash
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
```

**Problema**: "Permission denied: '/dev/ttyUSB0'"
```bash
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
```

---

## 📈 Roadmap

- [x] Análise offline de logs CSV
- [x] Telemetria CAN em tempo real
- [x] Telemetria LoRa com downsampling
- [x] Data logging local (CSV)
- [ ] Compressão de dados LoRa
- [ ] Dashboard web remoto
- [ ] Análise preditiva com ML

---

## 🤝 Contribuindo

Desenvolvido para a equipe PUCPR Racing Formula SAE.

---

## 📄 Licença

Open Source - PUCPR Racing

---

**Desenvolvido com ❤️ para PUCPR Racing Formula SAE** 🏎️💨
