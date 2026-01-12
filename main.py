#!/usr/bin/env python3
"""
PUCPR Racing - Ferramenta de Análise de Telemetria
Versão 2.0 - Estrutura Modular

Ponto de entrada principal da aplicação.
Para compatibilidade com versão anterior, use: python main_gui.py
"""

import customtkinter as ctk
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa constantes e configurações
from core.constants import configurar_estilo_matplotlib

# Importa a janela principal (que ainda está no main_gui.py por enquanto)
# Em breve será movida para gui/main_window.py
try:
    from main_gui import AppAnalisePUCPR
except ImportError:
    print("ERRO: Não foi possível importar AppAnalisePUCPR")
    print("Verifique se main_gui.py existe no diretório atual")
    sys.exit(1)


def main():
    """Função principal que inicializa a aplicação"""
    # Configura aparência global
    ctk.set_appearance_mode("dark")
    
    # Configura estilo do matplotlib
    configurar_estilo_matplotlib()
    
    # Cria e executa a aplicação
    app = AppAnalisePUCPR()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n✓ Aplicação encerrada pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
