# 🏎️ Guia Central de Telemetria - Raspberry Pi

## 📋 Visão Geral

O **central.py** é o sistema de telemetria que roda na **Raspberry Pi dentro do carro**. Ele:

1. ✅ **Lê dados CAN** da ECU a 50-100 Hz
2. ✅ **Aplica downsampling** (otimização de banda LoRa)
3. ✅ **Transmite via LoRa** para a Ground Station
4. ✅ **Grava CSV local** com todos os dados (backup)

---

## ⚙️ Pré-requisitos

### Hardware:
- Raspberry Pi 3/4 com Raspbian/Ubuntu
- Interface CAN (MCP2515 ou similar)
- Módulo LoRa Serial (E32, HC-12, etc)
- Cartão SD com 8GB+ (para logs)

### Software:
```bash
sudo apt update
sudo apt install python3-pip can-utils

pip3 install python-can cantools pyserial
```

---

## 🔧 Configuração

### 1. Configurar Interface CAN (SocketCAN)

**Ativar SPI** (se usar MCP2515):
```bash
sudo nano /boot/config.txt
```

Adicionar:
```
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25
```

Reiniciar:
```bash
sudo reboot
```

**Configurar CAN0**:
```bash
# Configurar a 500 kbps
sudo ip link set can0 type can bitrate 500000

# Ativar interface
sudo ip link set can0 up

# Verificar
ifconfig can0
```

Saída esperada:
```
can0: flags=193<UP,RUNNING,NOARP>  mtu 16
```

**Tornar permanente** (opcional):
```bash
sudo nano /etc/network/interfaces
```

Adicionar:
```
auto can0
iface can0 inet manual
    pre-up /sbin/ip link set can0 type can bitrate 500000
    up /sbin/ifconfig can0 up
    down /sbin/ifconfig can0 down
```

---

### 2. Configurar Módulo LoRa

**Conectar via USB**:
```bash
# Verificar porta
ls /dev/ttyUSB*
# Deve mostrar: /dev/ttyUSB0

# Dar permissões
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0
```

**Ou via GPIO** (UART):
```bash
# Desabilitar console serial
sudo raspi-config
# Interface Options → Serial → No (login shell) / Yes (serial port)

# Porta será: /dev/ttyAMA0
```

---

### 3. Configurar Arquivo DBC

Coloque o arquivo **pucpr.dbc** no mesmo diretório do central.py:
```bash
cd /home/pi/telemetria
cp pucpr.dbc .
```

Edite **central.py** se necessário (linha 47):
```python
DBC_FILE = 'pucpr.dbc'  # Ou caminho completo
```

---

## 🚀 Execução

### Modo Normal:
```bash
cd /home/pi/telemetria
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
[CSV] Iniciando gravação: ./logs/telemetria_pucpr_20260117_143025.csv

[Sistema] Iniciado com sucesso!
  CAN: can0 @ 500000 bps
  LoRa: /dev/ttyUSB0 @ 115200 baud
  Taxa de transmissão: 50 Hz (downsampling ativo)
  Data Logging: telemetria_pucpr_20260117_143025.csv

Pressione Ctrl+C para parar

------------------------------------------------------------
[Stats] Uptime: 5s
  LoRa TX: 250 pacotes | 50.0 Hz | 7.2 kbps
  CAN RX: 1523 mensagens
  Banda: 900 bytes/s (7.2 kbps)
  CSV Log: 250 amostras gravadas
------------------------------------------------------------
```

---

## ⚙️ Personalização

### Alterar Taxa de Transmissão LoRa

Edite **central.py** (linhas 52-54):
```python
# Taxas de transmissão (Hz)
RATE_HIGH_PRIORITY = 25     # Reduzir de 50 para 25 Hz
RATE_MEDIUM_PRIORITY = 5    # Reduzir de 10 para 5 Hz
RATE_LOW_PRIORITY = 1       # Manter em 1 Hz
```

**Recomendado para LoRa de longo alcance**: 15-25 Hz

---

### Alterar Porta Serial do LoRa

Edite **central.py** (linha 51):
```python
LORA_PORT = '/dev/ttyAMA0'  # GPIO UART
# ou
LORA_PORT = '/dev/ttyUSB0'  # USB Serial
```

---

### Desativar Data Logging

Edite **central.py** (linha 61):
```python
ENABLE_LOGGING = False  # Não grava CSV
```

---

### Alterar Diretório de Logs

Edite **central.py** (linha 60):
```python
LOG_DIRECTORY = '/media/usb/logs'  # USB externo
# ou
LOG_DIRECTORY = './logs'            # Diretório local
```

---

### Desativar Marcadores de Pacote LoRa

Edite **central.py** (linha 57):
```python
USE_PACKET_MARKERS = False  # Envia apenas payload (36 bytes)
```

Use `False` se a Ground Station não espera marcadores START/END.

---

## 🔍 Downsampling - Como Funciona

### Conceito:

```
┌─────────────────────────────────────────────────────────┐
│           ECU → CAN Bus (100 Hz)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │  central.py           │
         │  Lê TUDO a 100 Hz     │
         └───────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ↓                         ↓
┌───────────────┐         ┌──────────────┐
│  LoRa TX      │         │  CSV Log     │
│  50 Hz        │         │  100 Hz      │
│  Downsampling │         │  COMPLETO    │
└───────────────┘         └──────────────┘
```

### Prioridades:

| Prioridade | Taxa | Dados | Justificativa |
|------------|------|-------|---------------|
| **Alta** | 50 Hz | RPM, Suspensão, Aceleração, Volante, Freio | Variam rapidamente |
| **Média** | 10 Hz | TPS, Lambda, Velocidade Rodas | Variam moderadamente |
| **Baixa** | 1 Hz | Temperatura Motor | Varia lentamente |

### Economia de Banda:

- **Sem downsampling**: 36 bytes × 50 Hz = 1800 bytes/s = **14.4 kbps** ❌
- **Com downsampling**: 36 bytes × 50 Hz (60% cache) = ~900 bytes/s = **7.2 kbps** ✅

---

## 📊 Data Logging (CSV)

### Formato do Arquivo:

```csv
Timestamp_ms,Datetime,RPM,Temperatura,TPS,Lambda,SteeringAngle,BrakePressure,AccelX,AccelY,WheelSpeed_FL,WheelSpeed_FR,WheelSpeed_RL,WheelSpeed_RR,Suspension_FL,Suspension_FR,Suspension_RL,Suspension_RR
1705502425000,2026-01-17 14:30:25.000,3500,85,45,1.023,-12.5,15,0.523,-0.234,120,121,118,122,45,47,43,44
1705502425020,2026-01-17 14:30:25.020,3520,85,47,1.025,-12.3,16,0.531,-0.241,121,122,119,123,46,48,44,45
```

### Características:

- ✅ Grava **TODOS** os dados (sem downsampling)
- ✅ Taxa de amostragem: 50-100 Hz (igual à ECU)
- ✅ Flush automático a cada 100 amostras (não perde dados)
- ✅ Timestamp em ms + datetime legível
- ✅ Compatível com análise offline (main.py)

### Onde os Logs São Salvos:

```bash
./logs/telemetria_pucpr_YYYYMMDD_HHMMSS.csv
```

Exemplo:
```bash
./logs/telemetria_pucpr_20260117_143025.csv
./logs/telemetria_pucpr_20260117_150345.csv
```

### Gerenciar Logs:

```bash
# Listar logs
ls -lh logs/

# Ver tamanho ocupado
du -sh logs/

# Copiar para USB
sudo mount /dev/sda1 /mnt/usb
cp logs/*.csv /mnt/usb/

# Limpar logs antigos (mais de 7 dias)
find logs/ -name "*.csv" -mtime +7 -delete
```

---

## 🐛 Troubleshooting

### Problema: "CAN interface 'can0' not found"

**Solução**:
```bash
# Verificar interfaces
ip link show

# Configurar CAN
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up

# Verificar se está UP
ifconfig can0
```

---

### Problema: "Permission denied: '/dev/ttyUSB0'"

**Solução**:
```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER

# Dar permissão manual
sudo chmod 666 /dev/ttyUSB0

# Fazer logout e login novamente
```

---

### Problema: "DBC carregado: 0 mensagens"

**Causas**:
- Arquivo DBC não existe ou está vazio
- Caminho errado no `DBC_FILE`

**Solução**:
```bash
# Verificar se arquivo existe
ls -lh pucpr.dbc

# Testar carregamento manual
python3 -c "import cantools; db = cantools.database.load_file('pucpr.dbc'); print(f'{len(db.messages)} mensagens')"
```

---

### Problema: "LoRa TX: 0 Hz" (nenhum pacote enviado)

**Causas**:
- Porta serial errada
- LoRa não conectado

**Solução**:
```bash
# Verificar portas disponíveis
ls /dev/tty*

# Testar conexão serial
python3 -c "import serial; s = serial.Serial('/dev/ttyUSB0', 115200); print('OK'); s.close()"
```

---

### Problema: "Erro ao criar arquivo CSV"

**Causas**:
- Cartão SD cheio
- Diretório sem permissão de escrita

**Solução**:
```bash
# Verificar espaço
df -h

# Criar diretório manualmente
mkdir -p logs
chmod 777 logs
```

---

### Problema: "CAN RX: 0 mensagens" (não recebe dados)

**Causas**:
- ECU desligada
- Cabo CAN desconectado
- Bitrate incorreto

**Solução**:
```bash
# Monitorar barramento CAN
candump can0

# Verificar se há tráfego
cansniffer can0

# Alterar bitrate (se necessário)
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000  # 1 Mbps
sudo ip link set can0 up
```

---

## 🔄 Execução Automática (Systemd)

Para iniciar automaticamente ao ligar a Raspberry Pi:

### 1. Criar serviço:
```bash
sudo nano /etc/systemd/system/telemetria.service
```

### 2. Conteúdo:
```ini
[Unit]
Description=PUCPR Racing Telemetria Central
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/telemetria
ExecStartPre=/sbin/ip link set can0 type can bitrate 500000
ExecStartPre=/sbin/ip link set can0 up
ExecStart=/usr/bin/python3 /home/pi/telemetria/central.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. Ativar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telemetria.service
sudo systemctl start telemetria.service
```

### 4. Verificar status:
```bash
sudo systemctl status telemetria.service

# Ver logs
journalctl -u telemetria.service -f
```

---

## 📈 Monitoramento em Tempo Real

### Ver CAN Bus:
```bash
# Dump de todas as mensagens
candump can0

# Com timestamp
candump -t a can0

# Filtrar por ID (ex: Motor = 0x100)
candump can0,100:7FF
```

### Ver Logs CSV em Tempo Real:
```bash
tail -f logs/telemetria_pucpr_*.csv
```

---

## 🎯 Checklist Pré-Corrida

- [ ] CAN interface configurada e UP
- [ ] LoRa conectado e testado
- [ ] Arquivo DBC atualizado
- [ ] Cartão SD com espaço livre (>1GB)
- [ ] Teste de comunicação com Ground Station OK
- [ ] Logs anteriores copiados/removidos
- [ ] Bateria da Raspberry Pi carregada

---

## 📚 Arquivos Importantes

```
/home/pi/telemetria/
├── central.py           # Script principal
├── pucpr.dbc           # Definições CAN
├── logs/               # Logs CSV (criado automaticamente)
│   ├── telemetria_pucpr_20260117_143025.csv
│   └── telemetria_pucpr_20260117_150345.csv
└── README.md           # Documentação
```

---

## 🔧 Manutenção

### Atualizar Código:
```bash
cd /home/pi/telemetria
git pull
# ou
scp central.py pi@raspberrypi:/home/pi/telemetria/
```

### Backup de Logs:
```bash
# Via SCP (do PC)
scp -r pi@raspberrypi:/home/pi/telemetria/logs ./backup_logs/

# Via rsync
rsync -avz pi@raspberrypi:/home/pi/telemetria/logs/ ./backup_logs/
```

### Limpar Logs Antigos:
```bash
# Manual
rm logs/telemetria_pucpr_2026*.csv

# Automático (cron - diário às 3h)
crontab -e
```

Adicionar:
```
0 3 * * * find /home/pi/telemetria/logs -name "*.csv" -mtime +7 -delete
```

---

## 🏁 Dicas de Competição

1. **Teste antes da corrida**: Execute central.py no pit por 5 minutos
2. **Monitore a banda LoRa**: Se Hz < 40, reduza `RATE_HIGH_PRIORITY`
3. **Verifique espaço em disco**: 1 hora de corrida ≈ 500 MB de CSV
4. **Faça backup dos logs**: Copie para USB/Computador após cada sessão
5. **Use fonte estável**: Bateria dedicada para Raspberry Pi (não compartilhar com ECU)

---

**Desenvolvido para PUCPR Racing Formula SAE** 🏎️💨
