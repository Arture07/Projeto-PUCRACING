"""
Módulo GUI - Interface gráfica da aplicação PUCPR Racing

Fases implementadas:
- Fase 3: dashboards (Dashboards de tempo real)
- Fase 4: live_plotting (Sistema de plotagem ao vivo)

Fases pendentes:
- Fase 6: main_window (Classe principal - quando implementada)
"""

# Exporta apenas os módulos implementados
from . import dashboards
from . import live_plotting

__all__ = ['dashboards', 'live_plotting']
