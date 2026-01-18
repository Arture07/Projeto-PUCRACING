# PUCPR Racing - Sistema de Telemetria

Sistema completo de telemetria para carro de corrida, com **Ground Station (PC)** e **Central (Raspberry Pi)**.

## 📁 Estrutura do Projeto

```
Projeto PUCRACING/
│
├── docs/                          # 📄 Documentação
│   ├── README.md                  # Visão geral do projeto
│   ├── COMO_EXECUTAR.md          # Guia da Ground Station
│   └── GUIA_CENTRAL.md           # Guia da Raspberry Pi
│
├── ground_station/                # 🖥️ Ground Station (PC)
│   ├── main.py                   # Arquivo principal
│   ├── main_gui.py               # Interface gráfica
│   ├── calculations.py           # Cálculos de telemetria
│   ├── config_manager.py         # Gerenciamento de configurações
│   ├── data_loader.py            # Carregamento de dados
│   ├── plotting.py               # Gráficos e visualização
│   ├── simulador_carro.py        # Simulador de CAN Bus
│   ├── configure_telemetry.py    # Configurador de telemetria
│   ├── core/                     # Módulos principais
│   │   ├── constants.py          # Constantes do sistema
│   │   ├── lora_receiver.py      # Receptor LoRa
│   │   ├── telemetry_realtime.py # Telemetria em tempo real
│   │   └── analysis_callbacks.py # Callbacks de análise
│   └── gui/                      # Interface gráfica
│       ├── dashboards.py         # Dashboards
│       └── live_plotting.py      # Gráficos ao vivo
│
├── central/                       # 🔧 Central (Raspberry Pi)
│   └── central.py                # Sistema principal da Raspberry Pi
│
├── config/                        # ⚙️ Arquivos de Configuração
│   ├── config_pucpr_tool.ini     # Configurações da Ground Station
│   ├── pucpr.dbc                 # DBC padrão (100 Hz)
│   └── pucpr_alta_resolucao.dbc  # DBC alta resolução (detalhado)
│
├── data/                          # 📊 Dados de Exemplo
│   └── exemplo_log_pucpr_realista.csv
│
├── logs/                          # 📝 Logs da Central (gerados automaticamente)
│
└── requirements.txt              # 📦 Dependências do Python
```

## 🚀 Quick Start

### Ground Station (PC)

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Executar Ground Station
cd ground_station
python main.py
```

**Documentação completa:** [docs/COMO_EXECUTAR.md](docs/COMO_EXECUTAR.md)

### Central (Raspberry Pi)

```bash
# Na Raspberry Pi
cd central
python3 central.py
```

**Documentação completa:** [docs/GUIA_CENTRAL.md](docs/GUIA_CENTRAL.md)

## 📋 Pré-requisitos

- **Python 3.8+** (Windows/Linux)
- **Ambiente virtual** (.venv)
- **Raspberry Pi** com SocketCAN configurado (para Central)
- **Módulo LoRa** (para comunicação carro ↔ Ground Station)

## 📦 Instalação

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows)
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

## ⚙️ Funcionalidades

### Ground Station
- ✅ Interface gráfica com CustomTkinter
- ✅ Recepção via LoRa (Serial/USB)
- ✅ Gráficos em tempo real (RPM, temperatura, velocidades, suspensão)
- ✅ Exportação de dados CSV
- ✅ Simulador de carro incluído

### Central (Raspberry Pi)
- ✅ Recepção CAN Bus (SocketCAN)
- ✅ Downsampling inteligente (3 níveis de prioridade)
  - **Alta**: 50 Hz (RPM, suspensão, acelerômetro)
  - **Média**: 10 Hz (TPS, lambda, velocidades das rodas)
  - **Baixa**: 1 Hz (temperatura)
- ✅ Transmissão via LoRa otimizada (7.2 kbps)
- ✅ Data Logging completo (CSV com todos os dados a 50-100 Hz)
- ✅ Estatísticas em tempo real

## 🧪 Testando o Sistema

### Teste Local (Simulador)

```bash
# Terminal 1 - Simulador
cd ground_station
python simulador_carro.py

# Terminal 2 - Ground Station
cd ground_station
python main.py
```

### Teste Completo (Hardware Real)

1. Configure a Raspberry Pi (seguir [GUIA_CENTRAL.md](docs/GUIA_CENTRAL.md))
2. Conecte módulos LoRa (carro ↔ PC)
3. Execute `central.py` na Raspberry Pi
4. Execute `main.py` no PC

## 📖 Documentação

| Documento | Descrição |
|-----------|-----------|
| [README.md](docs/README.md) | Visão geral e arquitetura |
| [COMO_EXECUTAR.md](docs/COMO_EXECUTAR.md) | Executar Ground Station |
| [GUIA_CENTRAL.md](docs/GUIA_CENTRAL.md) | Configurar Raspberry Pi |

## 🔧 Configurações

### Arquivos DBC (CAN Database)
- **pucpr.dbc**: Configuração padrão (100 Hz)
- **pucpr_alta_resolucao.dbc**: Valores float com maior precisão

### Portas e Interfaces
- **Ground Station**: COM3-COM10 ou /dev/ttyUSB0 (LoRa)
- **Central**: can0 (CAN Bus), /dev/ttyUSB0 (LoRa)

## 📊 Formato de Dados CSV

Os logs são salvos em `logs/telemetria_pucpr_YYYYMMDD_HHMMSS.csv`:

```csv
Timestamp_ms,Datetime,RPM,Temperatura,TPS,Lambda,SteeringAngle,BrakePressure,AccelX,AccelY,WheelSpeed_FL,WheelSpeed_FR,WheelSpeed_RL,WheelSpeed_RR,Suspension_FL,Suspension_FR,Suspension_RL,Suspension_RR
```

## 🛠️ Troubleshooting

### Ground Station não conecta ao LoRa
- Verificar porta COM correta
- Checar baud rate (115200)
- Testar com simulador primeiro

### Central não recebe CAN
```bash
# Verificar interface CAN
ip link show can0
candump can0  # Testar recepção
```

### Logs CSV não são criados
- Verificar `ENABLE_LOGGING = True` em central.py
- Verificar permissões da pasta `logs/`
- Checar espaço em disco

## 🗺️ Roadmap

- [ ] Compressão de dados LoRa
- [ ] Dashboard web para monitoramento remoto
- [ ] Logging de GPS
- [ ] Validação de pacotes (CRC/checksum)
- [ ] Modo replay de dados

## 👥 Equipe

**PUCPR Racing** - Sistema de Telemetria Veicular

---

**Versão:** 2.0 (com Downsampling e Data Logging)  
**Última atualização:** Janeiro 2026
