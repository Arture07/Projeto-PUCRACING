# PUCPR Racing - Estrutura Modular do Projeto

## � Status da Modularização

| Fase | Status | Módulo | Linhas | Redução main_gui.py |
|------|--------|--------|--------|---------------------|
| 1 | ✅ CONCLUÍDA | `core/constants.py` | 26 | ~15 linhas |
| 2 | ✅ CONCLUÍDA | `core/analysis_callbacks.py` | 411 | ~400 linhas |
| 3 | ✅ CONCLUÍDA | `gui/dashboards.py` | 379 | ~200 linhas |
| 4 | ✅ CONCLUÍDA | `gui/live_plotting.py` | 482 | ~400 linhas |
| 5 | ✅ CONCLUÍDA | `core/telemetry_realtime.py` | 432 | ~330 linhas |
| 6 | 📦 OPCIONAL | `gui/main_window.py` | - | (refatoração avançada) |

**main_gui.py**: **2079 → 1142 linhas** (redução de **937 linhas / 45.1%**)  
**Código extraído**: **1730 linhas** em 5 novos módulos (Fases 1-5)  
**Aplicação testada e funcionando sem erros!** ✅

## �📁 Estrutura de Pastas

```
Projeto PUCRACING/
├── main_gui.py                      # 📦 Aplicação principal (1142 linhas - 45% menor!)
├── config_manager.py                # ⚙️ Gerenciamento de configurações
├── data_loader.py                   # 📂 Carregamento de dados
├── calculations.py                  # 📊 Cálculos matemáticos
├── plotting.py                      # 📈 Funções de plotagem
│
├── gui/                             # 🎨 Interface Gráfica
│   ├── __init__.py                  # Exporta dashboards e live_plotting
│   ├── dashboards.py                # ✅ Dashboards de tempo real (379 linhas)
│   └── live_plotting.py             # ✅ Sistema de plotagem ao vivo (482 linhas)
│
├── core/                            # ⚙️ Núcleo da Aplicação  
│   ├── __init__.py
│   ├── constants.py                 # ✅ Constantes e configurações visuais (26 linhas)
│   ├── analysis_callbacks.py       # ✅ Callbacks de análise avançadas (411 linhas)
│   └── telemetry_realtime.py       # ✅ Sistema CAN e telemetria em tempo real (432 linhas)
│
├── config_pucpr_tool.ini            # 🔧 Arquivo de configuração
├── pucpr.dbc                        # 🚗 Definição CAN
├── README.md                        # 📖 Documentação
└── ESTRUTURA_MODULAR.md             # 📋 Documentação da modularização

```

## 🔄 Migração Gradual

### Opção 1: Usar novo sistema modular
```python
from main import main  # Importa do novo sistema
main()
```

### Opção 2: Usar sistema legado (compatibilidade)
```python
python main_gui.py  # Funciona como antes
```

## 📦 Módulos

### `gui/main_window.py`
- Classe principal `AppAnalisePUCPR`
- Inicialização da janela
- Gerenciamento de tabs
- Carregamento de arquivos

### `gui/dashboards.py`
- Dashboards profissionais de tempo real
- Motor/ECU, Pilotagem, Rodas, Suspensão
- Progress bars e valores grandes

### `gui/live_plotting.py`
- Gráficos em tempo real
- Sistema de hover com tooltips
- Multi-eixos (até 4 canais)
- Freeze, auto-scroll, reset view

### `gui/analysis_tabs.py`
- Tab Geral/Plotagem
- Tab Skid Pad
- Tab Aceleração  
- Tab Autocross/Endurance


### `gui/dashboards.py` ✅ (379 linhas - Fase 3)
- **Dashboards profissionais de tempo real** para telemetria CAN ao vivo
- `criar_conteudo_dashboards_tempo_real()` - TabView com 4 sub-tabs
- `criar_dash_motor_ecu()` - **Motor/ECU Dashboard**
  - RPM: Fonte 56pt, progress bar, borda vermelha
  - Temperatura: 40pt
  - Lambda: 40pt
  - TPS: 32pt, progress bar dourado
- `criar_dash_pilotagem()` - **Pilotagem Dashboard**
  - Volante: 40pt, ângulo em graus
  - Freio: 40pt, progress bar vermelho, pressão em bar
  - IMU: AccelX e AccelY (36pt, dourado) em grid 1x2
- `criar_dash_rodas()` - **Rodas Dashboard (Grid 2x2)**
  - FL/FR: Borda dourada, 52pt
  - RL/RR: Borda vermelha, 52pt
  - Velocidades em km/h
- `criar_dash_suspensao()` - **Suspensão Dashboard (Grid 2x2)**
  - FL/FR: Borda ciano, 48pt
  - RL/RR: Borda verde, 48pt
  - Posições em mm
- `criar_card_sensor()` - Função legada para compatibilidade
- **Design**: Fontes grandes (48-56pt), progress bars, bordas coloridas, ícones Unicode

### `gui/live_plotting.py` ✅ (482 linhas - Fase 4)
- **Sistema completo de plotagem em tempo real** com interatividade avançada
- `format_hover_value()` - Formatação inteligente (≥1000: int, ≥100: 1 decimal, else 2 decimais)
- `hide_live_hover()` - Oculta linha vertical e tooltip
- `toggle_live_freeze()` - Congela/descongela renderização (mantém coleta de dados)
- `reset_live_view()` - Reset completo (zoom, pan, auto-scroll, hover)
- `apply_live_subplot_layout()` - Layout matplotlib (left=0.057, right=0.795/0.95)
- `setup_live_hover_artists()` - Cria crosshair + tooltip (bbox dourado)
- `on_live_plot_hover()` - **Tooltip interativo**:
  - Mostra valores de todos os canais no ponto do cursor
  - Respeita pan/zoom da toolbar
  - Tooltip com fundo tertiary, borda dourada
  - Clique para fixar/desafixar
- `toggle_auto_scroll()` - Janela rolante de 10 segundos
- `update_live_plot_style()` - **Reconfigura gráfico completo**:
  - **Modo Absoluto**: Eixo Y único, 4 cores (Red/Gold/Cyan/Green)
  - **Modo Normalizado**: Múltiplos eixos Y (twinx), spines coloridos offset (+60px, +120px)
  - Restaura dados históricos ao trocar de modo
  - Diferentes linestyles (-, --, -.) para distinção visual
- `abrir_seletor_canais_live()` - **Popup seletor de canais**:
  - 16 canais disponíveis (RPM, Temp, TPS, Lambda, Steering, Brake, AccelX/Y, 4x Wheels, 4x Suspension)
  - Máximo 4 canais simultâneos
  - Contador dinâmico "Selecionados: X/4"
  - Validação (warning se >4 ou 0)


### `core/telemetry_realtime.py` ✅ (432 linhas - Fase 5)
- **Sistema completo de telemetria CAN em tempo real**
- `toggle_live_telemetry()` - Alterna start/stop
- `start_live_telemetry()` - Inicia thread CAN + configuração inicial
- `stop_live_telemetry()` - Para thread e atualiza UI
- `loop_leitura_can()` - **Thread separada de leitura CAN**:
  - Carrega DBC (pucpr.dbc)
  - Conecta em UDP multicast (Windows) ou socketcan (Linux)
  - Decodifica mensagens CAN
  - Enfileira dados para GUI via queue
- `update_live_gui()` - **Atualização da GUI (10 FPS)**:
  - Processa fila de dados CAN
  - Sincroniza arrays de tempo + canais (padding automático)
  - Atualiza gráfico ao vivo (com slicing para performance)
  - Gerencia auto-scroll (janela de 10s)
  - Respeita freeze mode e toolbar pan/zoom
- `_update_dashboard_labels()` - **Atualiza todos os labels dos dashboards**:
  - RPM: valor + progress bar com cor dinâmica (verde/amarelo/vermelho)
  - TPS: valor + progress bar
  - Brake: valor + progress bar
  - Temperatura, Lambda, Steering, AccelX/Y
  - 4x Wheel Speeds, 4x Suspension Positions
  - Detecta e atualiza labels tanto da sidebar quanto dos dashboards
- **Dependências**: python-can, cantools, threading, queue

### `core/constants.py` ✅ (26 linhas)
- Paleta de cores (10 constantes)
- Configurações matplotlib
- Constante DEFAULT_FREQUENCY

### `core/analysis_callbacks.py` ✅ (520 linhas)
- **Tab Geral/Plotagem**: 4 funções
  - `mostrar_estatisticas_canais()` - Estatísticas descritivas
  - `comparar_voltas_gui()` - Interface de comparação
  - `_plotar_comparacao_voltas()` - Plot de comparação
  - `exportar_plot_atual()` - Exportação PNG/PDF/SVG
- **Tab Skid Pad**: 3 funções
  - `analisar_skidpad_completo()` - Análise G lateral, consistência, raio
  - `plotar_consistencia_skidpad()` - Gráfico de consistência
  - `detectar_secoes_skidpad()` - Detecção automática esquerda/direita
- **Tab Aceleração**: 3 funções
  - `analisar_aceleracao_completo()` - Multi-distância (25/50/75/100m)
  - `plotar_comparativo_aceleracao()` - Gráfico comparativo
  - `plotar_gforce_aceleracao()` - Análise G-Force longitudinal
- **Tab Autocross/Endurance**: 4 funções
  - `analisar_tempos_volta_completo()` - Estatísticas detalhadas
  - `analisar_setores_pista()` - Análise por setores
  - `plotar_heatmap_performance()` - Heatmap de velocidade
  - `comparar_voltas_detalhado()` - Comparação avançada

### `core/telemetry_realtime.py`
- Thread CAN
- Decodificação DBC
- Buffer de dados ao vivo

## 🎯 Benefícios da Modularização

1. **Manutenção mais fácil**: Cada arquivo tem responsabilidade clara
2. **Reutilização**: Módulos podem ser importados independentemente  
3. **Testes**: Mais fácil testar componentes isolados
4. **Colaboração**: Múltiplos desenvolvedores podem trabalhar simultaneamente
5. **Performance**: Imports seletivos carregam apenas o necessário

## 🚀 Status da Refatoração

A refatoração foi realizada de forma **gradual e não-destrutiva**:

### ✅ Concluído (Fases 1-5)
- ✅ **Fase 1**: Constantes extraídas para `core/constants.py` (26 linhas)
- ✅ **Fase 2**: Callbacks de análise extraídos para `core/analysis_callbacks.py` (411 linhas)
- ✅ **Fase 3**: Dashboards extraídos para `gui/dashboards.py` (379 linhas)
- ✅ **Fase 4**: Live plotting extraído para `gui/live_plotting.py` (482 linhas)
- ✅ **Fase 5**: Telemetria CAN extraída para `core/telemetry_realtime.py` (432 linhas)
- ✅ **main_gui.py reduzido de 2079 para 1142 linhas** (redução de 937 linhas / 45.1%)
- ✅ **5 módulos novos criados** com 1730 linhas de código organizado
- ✅ **Sem perda de funcionalidade** - Todas as features mantidas
- ✅ **Sem erros** - Aplicação testada e funcionando perfeitamente!

### 📦 Fase 6 (Opcional - Refatoração Avançada)
A **Fase 6** envolveria migrar a classe `AppAnalisePUCPR` completa para `gui/main_window.py`, transformando `main_gui.py` em apenas um launcher. Esta é uma refatoração mais avançada e não é necessária para o funcionamento da aplicação:
- Complexidade: Alta (migração completa da classe)
- Benefício: Modularidade teórica
- Impacto: Potenciais breaking changes
- Decisão: **Adiada** - A modularização atual (45% de redução) já atinge os objetivos

## 🎯 Benefícios da Modularização

1. **Manutenção mais fácil**: Cada arquivo tem responsabilidade clara
2. **Reutilização**: Módulos podem ser importados independentemente  
3. **Testes**: Mais fácil testar componentes isolados
4. **Colaboração**: Múltiplos desenvolvedores podem trabalhar simultaneamente
5. **Performance**: Imports seletivos carregam apenas o necessário
6. **Escalabilidade**: Fácil adicionar novas funcionalidades sem aumentar arquivo principal

## 📈 Métricas Finais

| Métrica | Antes | Depois | Mudança |
|---------|-------|--------|---------|
| **Linhas em main_gui.py** | 2079 | **1142** | **-937 (-45.1%)** |
| **Número de módulos** | 5 | **10** | **+5** |
| **Maior arquivo** | 2079 linhas | 1142 linhas | -45.1% |
| **Código modular** | 0% | **60.2%** | **+60.2%** |
| **Módulos criados** | - | **5 novos** | constants, analysis_callbacks, dashboards, live_plotting, telemetry_realtime |
| **Total extraído** | - | **1730 linhas** | Organizadas em módulos especializados |

### 📊 Distribuição de Código

|           Módulo             | Linhas | % do Total |     Responsabilidade     |
|------------------------------|--------|------------|--------------------------|
| `main_gui.py`                |  1142  | 39.8%      | Classe principal + UI    |
| `core/telemetry_realtime.py` |   432  | 15.0%      | Telemetria CAN + updates |
| `gui/live_plotting.py`       |   482  | 16.8%      | Plotagem interativa      |
| `core/analysis_callbacks.py` |   411  | 14.3%      | Análises avançadas       |
| `gui/dashboards.py`          |   379  | 13.2%      | Dashboards profissionais |
| `core/constants.py`          |    26  | 0.9%       | Constantes               |
| **TOTAL**                    |**2872**|  **100%**  |             -            |

## 🔧 Como Usar

A aplicação continua funcionando exatamente como antes:

```bash
python main.py
```

Os novos módulos são importados automaticamente:
```python
from core.constants import *
from core import analysis_callbacks, telemetry_realtime
from gui import dashboards, live_plotting
```

Nenhuma mudança necessária no workflow do usuário!

## ✅ Testes Realizados

- ✅ Aplicação inicia sem erros
- ✅ Importação de todos os módulos funcional
- ✅ Dashboards renderizando corretamente
- ✅ Live plotting operacional
- ✅ Telemetria CAN pronta (aguarda dados UDP)
- ✅ Análises funcionando (callbacks delegados)
- ✅ Sem breaking changes

## 🎉 Conclusão

A modularização foi **concluída com sucesso**! Reduzimos o arquivo principal em **45%**, criamos **5 módulos especializados** e organizamos **1730 linhas** de código. A aplicação está **testada, funcional e sem erros**.

**Próximos passos sugeridos** (opcionais):
- Fase 7: Separar análises específicas (gg_diagram.py, lap_detection.py, etc)
- Testes unitários para cada módulo
- Documentação de API para desenvolvedores


- ✅ Estrutura de pastas criada (gui/, core/)
- ✅ Constantes extraídas (core/constants.py - 41 linhas)
- ✅ Callbacks de análise migrados (core/analysis_callbacks.py - 520 linhas)
- ✅ Novo main.py criado (54 linhas)
- ✅ **Redução**: main_gui.py de 2425 → 2082 linhas (343 linhas = 14.1%)

### 🔄 Próximos Passos
- ⏳ Migração de dashboards (gui/dashboards.py)
- ⏳ Migração de live plotting (gui/live_plotting.py)
- ⏳ Migração de telemetria CAN (core/telemetry_realtime.py)
- ⏳ Migração da classe principal (gui/main_window.py)

**O arquivo `main_gui.py` original será mantido** para garantir compatibilidade durante a transição.
