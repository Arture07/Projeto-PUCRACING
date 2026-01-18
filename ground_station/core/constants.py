"""
Constantes e configurações visuais da aplicação
"""

import matplotlib.pyplot as plt

# Paleta de cores refinada
COLOR_BG_PRIMARY = "#242424"    # Fundo principal um pouco mais escuro
COLOR_BG_SECONDARY = "#1F1F1F"  # Fundo secundário (sidebar, tabs)
COLOR_BG_TERTIARY = "#2B2B2B"   # Fundo para elementos internos (scrollframe, plot)
COLOR_ACCENT_RED = "#D32F2F"    # Vermelho um pouco menos saturado
COLOR_ACCENT_GOLD = "#FBC02D"   # Dourado/Amarelo para destaque secundário
COLOR_ACCENT_CYAN = "#00E5FF"   # Ciano para destaque frontal (suspensão)
COLOR_ACCENT_GREEN = "#76FF03"  # Verde para destaque traseiro (suspensão)
COLOR_TEXT_PRIMARY = "#F5F5F5"  # Texto principal (quase branco)
COLOR_TEXT_SECONDARY = "#BDBDBD" # Texto secundário (cinza claro)
COLOR_BORDER = "#424242"        # Cor para bordas sutis

# Frequência padrão (usada se timestamp falhar)
DEFAULT_FREQUENCY = 50  # Hz

def configurar_estilo_matplotlib():
    """Configura o estilo global do matplotlib"""
    plt.style.use('dark_background')
    plt.rc('axes', facecolor=COLOR_BG_TERTIARY, edgecolor=COLOR_BORDER, 
           labelcolor=COLOR_TEXT_SECONDARY, titlecolor=COLOR_TEXT_PRIMARY)
    plt.rc('figure', facecolor=COLOR_BG_SECONDARY)
    plt.rc('xtick', color=COLOR_TEXT_SECONDARY)
    plt.rc('ytick', color=COLOR_TEXT_SECONDARY)
    plt.rc('grid', color=COLOR_BORDER, linestyle='--', alpha=0.7)
    plt.rc('text', color=COLOR_TEXT_PRIMARY)
    plt.rc('legend', facecolor=COLOR_BG_SECONDARY, edgecolor=COLOR_BORDER, 
           labelcolor=COLOR_TEXT_PRIMARY)
