# 📡 Sistema de Telemetria LoRa - PUCPR Racing

## 📋 Resumo

O projeto agora suporta **duas fontes de telemetria em tempo real**:

1. **CAN Bus** (original): Via UDP Multicast ou SocketCAN + DBC
2. **LoRa Serial** (novo): Via porta USB com receptor LoRa

## 🏗️ Arquitetura da Comunicação

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUCPR Racing - Telemetria                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐                      ┌──────────────────────┐
│  CARRO (Central) │                      │  GROUND STATION (PC) │
│  Raspberry Pi    │                      │   Windows/Linux      │
├──────────────────┤                      ├──────────────────────┤
│                  │                      │                      │
│  1. Lê sensores  │                      │  4. Recebe pacotes   │
│     CAN Bus      │                      │     via Serial       │
│                  │    LoRa 433/915MHz   │                      │
│  2. Empacota     │◄────────────────────►│  5. Desempacota      │
│     struct (36B) │    **SEM FIOS**      │     struct           │
│                  │                      │                      │
│  3. Transmite    │                      │  6. Atualiza         │
│     via LoRa TX  │                      │     Dashboard        │
│                  │                      │                      │
└──────────────────┘                      └──────────────────────┘
       ▲                                            ▲
       │                                            │
   Sensores:                                  Receptor LoRa
   - RPM                                       USB (CH340/FTDI)
   - Temperatura                               
   - TPS, Lambda                               
   - Freio, Volante                            
   - 4x Rodas                                  
   - 4x Suspensão                              
   - IMU (AccelX/Y)                            
```

## 📦 Protocolo de Comunicação

### Struct Binária (36 bytes)

A **Central (Raspberry Pi)** envia via LoRa um pacote compactado:

```c
struct TelemetryPacket {
    uint16_t rpm;           // 0-13000 RPM
    int8_t temperatura;     // -40 a 125°C
    uint8_t tps;            // 0-100%
    uint16_t lambda;        // 0-2000 (div 1000 = 0.0-2.0)
    int16_t steeringAngle;  // -500 a 500 (div 10 = -50.0 a 50.0°)
    uint16_t brakePressure; // 0-200 bar
    int16_t accelX;         // -3000 a 3000 (div 1000 = -3.0 a 3.0 G)
    int16_t accelY;         // -3000 a 3000 (div 1000 = -3.0 a 3.0 G)
    uint16_t wheelFL;       // 0-300 km/h
    uint16_t wheelFR;
    uint16_t wheelRL;
    uint16_t wheelRR;
    uint16_t suspFL;        // 0-200 mm
    uint16_t suspFR;
    uint16_t suspRL;
    uint16_t suspRR;
    uint32_t timestamp;     // milissegundos desde boot
} __attribute__((packed));  // Total: 36 bytes
```

**Formato de transmissão**:
- Little-endian (LSB primeiro)
- Sem padding (packed struct)
- Taxa típica: 10-50 Hz

## 🔧 Configuração da Ground Station

### 1. Instalar Dependências

```bash
pip install pyserial
```

### 2. Conectar Hardware

1. **Conecte o receptor LoRa** na porta USB do PC
2. **Identifique a porta**:
   - **Windows**: Gerenciador de Dispositivos → Portas (COM3, COM4, etc)
   - **Linux**: `ls /dev/ttyUSB*` ou `dmesg | grep tty`

### 3. Configurar Fonte de Telemetria

Execute o configurador interativo:

```bash
python configure_telemetry.py
```

**Saída esperada**:
```
============================================================
   CONFIGURADOR DE FONTE DE TELEMETRIA - PUCPR Racing
============================================================

Fontes disponíveis:

  [1] CAN Bus (UDP Multicast)
      Recebe mensagens CAN via rede UDP (Windows)

  [2] CAN Bus (SocketCAN)
      Recebe mensagens CAN diretamente (Linux/Raspberry Pi)

  [3] LoRa (Serial USB)
      Recebe pacotes LoRa via porta serial

  [4] Simulador CAN
      Dados simulados para testes (rodar simulador_carro.py)

Fonte atual: Simulador CAN

Escolha uma fonte (1-4) ou 'q' para sair: 3

✓ Selecionado: LoRa (Serial USB)
Confirmar? (s/n): s

✓ Configuração salva: LoRa (Serial USB)

------------------------------------------------------------
PRÓXIMOS PASSOS:
------------------------------------------------------------
1. Conecte o receptor LoRa na porta USB
2. Verifique a porta no Gerenciador de Dispositivos (Windows)
   ou rode: ls /dev/ttyUSB* (Linux)
3. Inicie a aplicação: python main.py
4. Clique em 'Iniciar Telemetria' na aba Tempo Real
------------------------------------------------------------
```

### 4. Executar Aplicação

```bash
python main.py
```

1. Vá na aba **"Tempo Real"**
2. Clique **"▶️ Iniciar Telemetria"**
3. O sistema irá:
   - Auto-detectar a porta serial (ou pedir para configurar)
   - Conectar ao receptor LoRa
   - Começar a receber pacotes
   - Atualizar dashboards em tempo real

## 📊 Módulo Criado

### [`core/lora_receiver.py`](core/lora_receiver.py) (450 linhas)

**Classe principal**: `LoRaReceiver`

**Funcionalidades**:
- ✅ Auto-detecção de porta serial (busca por CH340, FTDI, CP210x)
- ✅ Conexão Serial configurável (padrão: 115200 baud)
- ✅ Thread de recepção em background (não trava GUI)
- ✅ Desempacotamento de struct binária (36 bytes)
- ✅ Conversão automática de escalas (lambda/1000, steering/10, etc)
- ✅ Buffer thread-safe para GUI
- ✅ Estatísticas de recepção (Hz, pacotes OK/erro, uptime)
- ✅ Integração com dashboards existentes (reutiliza `_update_dashboard_labels`)
- ✅ Integração com gráfico ao vivo (reutiliza `update_live_plot_style`)

**Funções de integração**:
- `start_lora_telemetry(app_instance, port)` - Inicia recepção
- `stop_lora_telemetry(app_instance)` - Para recepção
- `update_lora_gui(app_instance)` - Atualiza GUI (chamado a cada 100ms)

## 🧪 Teste Standalone

Para testar o receptor LoRa **sem a GUI**:

```bash
python -m core.lora_receiver
```

**Saída esperada**:
```
=== Teste do Receptor LoRa ===

Portas seriais disponíveis:
  COM3: USB-SERIAL CH340 (COM3)
  COM4: Arduino Uno (COM4)

[LoRa] Porto detectado: COM3 (USB-SERIAL CH340)
[LoRa] Conectado em COM3 @ 115200 baud
[LoRa] Thread de recepção iniciada
Recebendo dados... (Ctrl+C para parar)

[ 25.3 Hz] RPM= 3450 | Temp= 85°C | TPS= 45% | Brake= 12 bar
[ 26.1 Hz] RPM= 3520 | Temp= 86°C | TPS= 47% | Brake= 15 bar
[ 25.8 Hz] RPM= 3610 | Temp= 86°C | TPS= 50% | Brake= 18 bar
...
```

## 🔍 Comparação CAN vs LoRa

| Característica | CAN Bus (UDP/SocketCAN) | LoRa Serial |
|----------------|-------------------------|-------------|
| **Alcance** | Limitado (rede local) | Até 2-15 km |
| **Latência** | Baixa (~5ms) | Média (~50-200ms) |
| **Taxa de dados** | Alta (até 1 Mbps) | Baixa (0.3-50 kbps) |
| **Consumo** | Alto | Muito baixo |
| **Infraestrutura** | Requer rede ou cabo CAN | Sem fios |
| **Uso ideal** | Pit/oficina, testes | Corrida ao vivo |
| **Configuração** | DBC file necessário | Struct fixa |

## ⚙️ Personalização

### Alterar Taxa de Transmissão LoRa

Edite [`core/lora_receiver.py`](core/lora_receiver.py):

```python
BAUD_RATE = 115200  # Altere para 9600, 57600, etc
```

### Adicionar Marcadores de Pacote

Se a Central enviar marcadores START/END (ex: 0xAA55 ... 0x55AA):

Em [`core/lora_receiver.py`](core/lora_receiver.py), método `read_packet()`, **descomente**:

```python
# Busca marcador de início
while self.running:
    if self.serial_conn.read(1) == START_MARKER[0]:
        if self.serial_conn.read(1) == START_MARKER[1]:
            payload = self.serial_conn.read(PACKET_SIZE)
            end = self.serial_conn.read(len(END_MARKER))
            if end == END_MARKER:
                return payload
```

### Modificar Struct de Dados

Se a Central usar struct diferente:

1. Edite `STRUCT_FORMAT` em [`lora_receiver.py`](core/lora_receiver.py)
2. Atualize `PACKET_SIZE`
3. Modifique `unpack_packet()` conforme novos campos

## 🐛 Troubleshooting

### "Nenhuma porta serial encontrada"
- Verifique se o receptor LoRa está conectado
- Instale drivers (CH340, FTDI, CP210x)
- Windows: Gerenciador de Dispositivos
- Linux: `sudo usermod -a -G dialout $USER` (adiciona usuário ao grupo dialout)

### "Tamanho inválido: X bytes"
- A Central está enviando pacotes incompletos
- Verifique taxa de transmissão LoRa (deve ser igual em TX e RX)
- Considere adicionar marcadores START/END

### "Erro ao desempacotar"
- Struct da Central diferente da configurada
- Verifique `STRUCT_FORMAT` (little-endian vs big-endian)
- Use ferramenta hex para inspecionar bytes recebidos

### Dashboard não atualiza
- Verifique se selecionou fonte "LoRa" no configurador
- Confirme que `lbl_live_status` mostra "LoRa X.X Hz"
- Teste standalone: `python -m core.lora_receiver`

## 📈 Próximos Passos

- [ ] Adicionar checksum/CRC para validação de pacotes
- [ ] Implementar compressão de dados
- [ ] Gravar logs LoRa em arquivo (mesmo formato CSV)
- [ ] Interface para configurar porta serial pela GUI
- [ ] Suporte a múltiplos receptores LoRa simultâneos

## 📄 Licença

Parte do projeto PUCPR Racing - Open Source

---

**Desenvolvido para a equipe PUCPR Racing Formula SAE** 🏎️💨
