# 🚀 Início Rápido - PUCPR Racing

## ⚡ Execução Ground Station (PC)

```bash
# Opção 1: Com ambiente virtual ativado
.venv\Scripts\activate
cd ground_station
python main.py

# Opção 2: Sem ativar ambiente (recomendado)
cd ground_station
& "C:/Users/akmar/Documents/Curso_TI/Projeto PUCRACING/.venv/Scripts/python.exe" main.py

# Opção 3: Mais simples (do diretório raiz)
cd ground_station
..\\.venv\Scripts\python.exe main.py
```

## 🧪 Testar com Simulador

```bash
# Terminal 1 - Simulador
cd ground_station
..\\.venv\Scripts\python.exe simulador_carro.py

# Terminal 2 - Ground Station
cd ground_station
..\\.venv\Scripts\python.exe main.py
```

## 🔧 Execução Central (Raspberry Pi)

```bash
# Na Raspberry Pi
cd central
sudo python3 central.py
```

> **Nota:** Requer configuração prévia do SocketCAN. Veja [docs/GUIA_CENTRAL.md](docs/GUIA_CENTRAL.md)

## 📖 Documentação Completa

| Guia | Descrição |
|------|-----------|
| [README.md](README.md) | Estrutura do projeto |
| [docs/COMO_EXECUTAR.md](docs/COMO_EXECUTAR.md) | Ground Station detalhado |
| [docs/GUIA_CENTRAL.md](docs/GUIA_CENTRAL.md) | Central (Raspberry Pi) |

## ❓ Problemas?

### ❌ Erro: `ModuleNotFoundError`
```bash
pip install -r requirements.txt
```

### ❌ Ground Station não abre
- Verificar ambiente virtual ativado
- Executar de dentro da pasta `ground_station/`

### ❌ Simulador não envia dados
- Configurar porta serial correta (COM3-COM10)
- Usar cabo loop-back ou virtual serial

---

**Versão rápida - Para detalhes, consulte a documentação completa em `docs/`**
