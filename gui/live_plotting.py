"""
Módulo de plotagem em tempo real (Live Plotting) para telemetria CAN.
Contém funções para gerenciamento do gráfico ao vivo, hover interativo, e controles.
"""

import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from core.constants import (
    COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
    COLOR_ACCENT_RED, COLOR_ACCENT_GOLD,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER
)


def format_hover_value(v):
    """Formata valores para exibição no tooltip do hover."""
    if v is None:
        return "N/A"
    try:
        av = abs(float(v))
    except (ValueError, TypeError):
        return str(v)
    
    if av >= 1000:
        return f"{v:.0f}"
    if av >= 100:
        return f"{v:.1f}"
    return f"{v:.2f}"


def hide_live_hover(app_instance):
    """Oculta os elementos visuais do hover (linha vertical e tooltip)."""
    if app_instance._live_hover_vline is not None:
        try:
            app_instance._live_hover_vline.set_visible(False)
        except Exception:
            pass
    if app_instance._live_hover_text is not None:
        try:
            app_instance._live_hover_text.set_visible(False)
        except Exception:
            pass


def toggle_live_freeze(app_instance):
    """Congela/descongela apenas o redesenho do gráfico ao vivo."""
    try:
        app_instance.live_freeze = bool(app_instance.switch_freeze.get() == 1)
        if app_instance.live_freeze:
            app_instance.lbl_live_status.configure(text="Status: Congelado (recebendo dados)")
        else:
            # Volta ao status padrão na próxima atualização
            pass
    except Exception:
        pass


def reset_live_view(app_instance):
    """Volta para a visão padrão (auto-scroll, sem freeze, sem pin)."""
    try:
        app_instance.live_freeze = False
        if hasattr(app_instance, 'switch_freeze'):
            app_instance.switch_freeze.deselect()

        app_instance.auto_scroll = True
        if hasattr(app_instance, 'switch_auto_scroll'):
            app_instance.switch_auto_scroll.select()

        # Desfixa tooltip
        app_instance._live_hover_pinned = False
        app_instance._live_hover_pinned_idx = None
        hide_live_hover(app_instance)

        # Reseta zoom/pan do matplotlib (se disponível)
        if hasattr(app_instance, 'toolbar_live'):
            try:
                app_instance.toolbar_live.home()
            except Exception:
                pass

        app_instance.canvas_live.draw_idle()
    except Exception:
        pass


def apply_live_subplot_layout(app_instance, n_channels, use_normalization):
    """Aplica um layout consistente (equivalente ao subplot tool) no gráfico ao vivo."""
    try:
        left = 0.057
        bottom = 0.07
        top = 0.945

        if use_normalization:
            # Espaço extra na direita para múltiplos eixos
            right = 0.795
        else:
            right = 0.95

        app_instance.fig_live.subplots_adjust(left=left, bottom=bottom, right=right, top=top)
    except Exception:
        pass


def setup_live_hover_artists(app_instance):
    """(Re)cria os elementos visuais do hover no gráfico ao vivo.
    
    Precisa ser chamado após limpar/recriar a figura/axes.
    """
    app_instance._live_hover_last_idx = None
    app_instance._live_hover_pinned = False
    app_instance._live_hover_pinned_idx = None
    try:
        # Linha vertical no eixo principal
        app_instance._live_hover_vline = app_instance.ax_live.axvline(
            0,
            color=COLOR_TEXT_SECONDARY,
            alpha=0.35,
            linewidth=1.0,
            linestyle='--',
            zorder=1,
            visible=False,
        )
    except Exception:
        app_instance._live_hover_vline = None

    try:
        # Caixa de texto no Figure (coordenadas normalizadas 0..1)
        app_instance._live_hover_text = app_instance.fig_live.text(
            0.02,
            0.02,
            "",
            transform=app_instance.fig_live.transFigure,
            ha='left',
            va='bottom',
            fontsize=10,
            color=COLOR_TEXT_PRIMARY,
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor=COLOR_BG_TERTIARY,
                edgecolor=COLOR_ACCENT_GOLD,
                alpha=0.92,
            ),
            zorder=10,
        )
        app_instance._live_hover_text.set_visible(False)
    except Exception:
        app_instance._live_hover_text = None


def on_live_plot_hover(app_instance, event):
    """Mostra tooltip com valores dos canais selecionados no X do cursor."""
    try:
        # Não atrapalhar pan/zoom da toolbar
        if hasattr(app_instance, 'toolbar_live') and getattr(app_instance.toolbar_live, 'mode', ''):
            hide_live_hover(app_instance)
            app_instance.canvas_live.draw_idle()
            return

        # Se estiver fixado por clique, não atualiza no movimento
        if app_instance._live_hover_pinned:
            return

        if event is None or event.inaxes is None or event.xdata is None:
            hide_live_hover(app_instance)
            app_instance.canvas_live.draw_idle()
            return

        if 'Time' not in app_instance.live_data_storage:
            hide_live_hover(app_instance)
            app_instance.canvas_live.draw_idle()
            return

        t_list = app_instance.live_data_storage.get('Time', [])
        if not t_list or len(t_list) < 2:
            hide_live_hover(app_instance)
            app_instance.canvas_live.draw_idle()
            return

        x = float(event.xdata)
        t_arr = np.asarray(t_list, dtype=float)
        idx = int(np.searchsorted(t_arr, x, side='left'))
        if idx <= 0:
            idx = 0
        elif idx >= len(t_arr):
            idx = len(t_arr) - 1
        else:
            # Escolhe o mais próximo entre idx-1 e idx
            if abs(t_arr[idx] - x) > abs(x - t_arr[idx - 1]):
                idx = idx - 1

        if app_instance._live_hover_last_idx == idx and app_instance._live_hover_text is not None and app_instance._live_hover_text.get_visible():
            return
        app_instance._live_hover_last_idx = idx

        t_val = t_arr[idx]
        lines = [f"t = {t_val:.2f} s"]
        for canal in app_instance.selected_live_channels:
            y_list = app_instance.live_data_storage.get(canal)
            if not y_list or idx >= len(y_list):
                continue
            y_val = y_list[idx]
            lines.append(f"{canal}: {format_hover_value(y_val)}")

        # Atualiza posição da linha
        if app_instance._live_hover_vline is not None:
            app_instance._live_hover_vline.set_xdata([t_val, t_val])
            app_instance._live_hover_vline.set_visible(True)

        # Atualiza texto
        if app_instance._live_hover_text is not None:
            app_instance._live_hover_text.set_text("\n".join(lines))
            app_instance._live_hover_text.set_visible(True)

        app_instance.canvas_live.draw_idle()

    except Exception:
        pass


def toggle_auto_scroll(app_instance):
    """Alterna o estado do auto-scroll."""
    if app_instance.switch_auto_scroll.get() == 1:
        app_instance.auto_scroll = True
    else:
        app_instance.auto_scroll = False

        # Ao desligar, abre o eixo X para facilitar navegar no histórico
        try:
            t_data = app_instance.live_data_storage.get('Time', [])
            if t_data and len(t_data) >= 2:
                app_instance.ax_live.set_xlim(0, t_data[-1])
                app_instance.canvas_live.draw_idle()
        except Exception:
            pass


def update_live_plot_style(app_instance):
    """Reconfigura completamente o gráfico ao vivo com base nos canais selecionados."""
    print(f"[DEBUG] update_live_plot_style chamado. Canais: {app_instance.selected_live_channels}")
    
    # Limpa completamente a figura
    app_instance.fig_live.clf()
    app_instance.ax_live = app_instance.fig_live.add_subplot(111)
    app_instance.live_lines = {}
    app_instance.live_axes = {}
    
    # Configuração base do eixo X
    app_instance.ax_live.set_xlabel('Tempo (s)', color=COLOR_TEXT_SECONDARY, fontsize=9)
    app_instance.ax_live.grid(True, linestyle='--', alpha=0.3, color=COLOR_BORDER)
    app_instance.ax_live.tick_params(axis='x', colors=COLOR_TEXT_SECONDARY, labelsize=8)
    app_instance.ax_live.set_facecolor(COLOR_BG_SECONDARY)
    
    use_normalization = (app_instance.switch_normalize.get() == 1)
    n_channels = len(app_instance.selected_live_channels)

    # Layout fixo (tamanho/margens) para combinar com o ajuste manual do subplot tool
    apply_live_subplot_layout(app_instance, n_channels=n_channels, use_normalization=use_normalization)
    
    # Cores distintas para cada canal
    colors = ["#FF3B30", "#FFD60A", "#00E5FF", "#76FF03"]  # Vermelho, Dourado, Ciano, Verde
    
    if not use_normalization:
        # ===== MODO ABSOLUTO (Eixo Y único) =====
        app_instance.ax_live.set_title("Monitoramento em Tempo Real (Absoluto)", 
                                       color=COLOR_TEXT_PRIMARY, fontsize=10, pad=10)
        app_instance.ax_live.set_ylabel('Valor', color=COLOR_TEXT_SECONDARY, fontsize=9)
        app_instance.ax_live.tick_params(axis='y', colors=COLOR_TEXT_SECONDARY, labelsize=8)
        
        for i, canal in enumerate(app_instance.selected_live_channels):
            color = colors[i % len(colors)]
            line, = app_instance.ax_live.plot([], [], label=canal, color=color, 
                                             linewidth=2.0, alpha=0.9)
            app_instance.live_lines[canal] = line
            app_instance.live_axes[canal] = app_instance.ax_live
            
            # Restaura dados históricos se existirem
            if canal in app_instance.live_data_storage and 'Time' in app_instance.live_data_storage:
                t_data = app_instance.live_data_storage['Time']
                y_data = app_instance.live_data_storage[canal]
                if len(t_data) == len(y_data) and len(t_data) > 0:
                    line.set_data(t_data, y_data)
        
        # Ajusta limites
        app_instance.ax_live.relim()
        app_instance.ax_live.autoscale_view()
        
    else:
        # ===== MODO NORMALIZADO (Múltiplos Eixos Y) =====
        app_instance.ax_live.set_title("Monitoramento em Tempo Real (Escalas Ajustadas)", 
                                       color=COLOR_TEXT_PRIMARY, fontsize=10, pad=10)

        # Mantém o layout definido em apply_live_subplot_layout
        
        host = app_instance.ax_live
        host.set_facecolor(COLOR_BG_SECONDARY)
        
        # Primeiro canal sempre no eixo host
        color0 = colors[0]
        host.set_ylabel(app_instance.selected_live_channels[0], color=color0, 
                       fontsize=9, fontweight='bold')
        host.tick_params(axis='y', labelcolor=color0, colors=color0, labelsize=8)
        host.yaxis.label.set_color(color0)
        
        line0, = host.plot([], [], color=color0, linewidth=2.0, 
                          label=app_instance.selected_live_channels[0], alpha=0.95)
        app_instance.live_lines[app_instance.selected_live_channels[0]] = line0
        app_instance.live_axes[app_instance.selected_live_channels[0]] = host
        
        # Restaura dados do primeiro canal
        if app_instance.selected_live_channels[0] in app_instance.live_data_storage and 'Time' in app_instance.live_data_storage:
            t_data = app_instance.live_data_storage['Time']
            y_data = app_instance.live_data_storage[app_instance.selected_live_channels[0]]
            if len(t_data) == len(y_data) and len(t_data) > 0:
                line0.set_data(t_data, y_data)
                host.relim()
                host.autoscale_view()
                # Adiciona margem vertical diferenciada para cada canal
                host.margins(y=0.15)
        
        # Cria eixos adicionais e plota
        for i in range(1, n_channels):
            canal = app_instance.selected_live_channels[i]
            color = colors[i % len(colors)]
            
            # Cria eixo twin
            ax = host.twinx()
            
            # CRÍTICO: Faz o eixo completamente transparente
            ax.set_frame_on(False)
            ax.patch.set_visible(False)
            
            # Posiciona o spine direito
            if i == 1:
                pass  # Posição padrão
            elif i == 2:
                ax.spines['right'].set_position(('outward', 60))
            elif i == 3:
                ax.spines['right'].set_position(('outward', 120))
            
            # Configuração visual
            ax.set_ylabel(canal, color=color, fontsize=9, fontweight='bold')
            ax.tick_params(axis='y', labelcolor=color, colors=color, labelsize=8)
            ax.yaxis.label.set_color(color)
            ax.spines['right'].set_edgecolor(color)
            ax.spines['right'].set_linewidth(2.0)  # Spine mais grosso
            ax.spines['right'].set_visible(True)
            
            # Remove outros spines
            ax.spines['left'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            
            # Sem grid
            ax.grid(False)
            
            # Plota linha mais GROSSA e com traço diferente para distinguir
            linestyles = ['-', '-', '--', '-.']  # Sólido, Sólido, Tracejado, Traço-ponto
            line, = ax.plot([], [], color=color, linewidth=2.5, label=canal, 
                           alpha=0.98, linestyle=linestyles[i])
            app_instance.live_lines[canal] = line
            app_instance.live_axes[canal] = ax
            
            # Restaura dados
            if canal in app_instance.live_data_storage and 'Time' in app_instance.live_data_storage:
                t_data = app_instance.live_data_storage['Time']
                y_data = app_instance.live_data_storage[canal]
                if len(t_data) == len(y_data) and len(t_data) > 0:
                    line.set_data(t_data, y_data)
                    ax.relim()
                    ax.autoscale_view()
                    # Margem vertical progressiva para "espalhar" as linhas visualmente
                    margin = 0.15 + (i * 0.05)
                    ax.margins(y=margin)
    
    # ===== LEGENDA UNIVERSAL =====
    all_lines = []
    all_labels = []
    
    for canal in app_instance.selected_live_channels:
        if canal in app_instance.live_lines:
            all_lines.append(app_instance.live_lines[canal])
            all_labels.append(canal)
    
    if all_lines:
        legend = app_instance.ax_live.legend(
            all_lines,
            all_labels,
            loc='upper left',
            fontsize=9,
            facecolor=COLOR_BG_TERTIARY,
            edgecolor=COLOR_ACCENT_GOLD,
            framealpha=0.92,
            shadow=True
        )
        # Força cor branca no texto da legenda
        for text in legend.get_texts():
            text.set_color('#FFFFFF')
    
    # Recria elementos do hover (a figura foi limpa)
    setup_live_hover_artists(app_instance)

    print(f"[DEBUG] Gráfico reconfigurado com {len(app_instance.live_lines)} linhas.")
    app_instance.canvas_live.draw_idle()


def abrir_seletor_canais_live(app_instance):
    """Abre uma janela popup para selecionar os canais do gráfico em tempo real."""
    canais_possiveis = sorted(['RPM', 'Temperatura', 'ThrottlePos', 'Lambda', 
                               'SteeringAngle', 'BrakePressure', 'AccelX', 'AccelY',
                               'WheelSpeed_FL', 'WheelSpeed_FR', 'WheelSpeed_RL', 'WheelSpeed_RR',
                               'SuspensionPos_FL', 'SuspensionPos_FR', 'SuspensionPos_RL', 'SuspensionPos_RR'])
    
    popup = ctk.CTkToplevel(app_instance)
    popup.title("Selecionar Canais - Live Plot")
    popup.geometry("320x450")
    popup.grab_set()
    
    lbl = ctk.CTkLabel(popup, text="Selecione até 4 canais:", font=app_instance.DEFAULT_FONT_BOLD)
    lbl.pack(pady=10)
    
    # Label para mostrar quantos estão selecionados
    lbl_count = ctk.CTkLabel(popup, text=f"Selecionados: {len(app_instance.selected_live_channels)}/4", 
                             font=app_instance.SMALL_FONT)
    lbl_count.pack(pady=5)
    
    frame_scroll = ctk.CTkScrollableFrame(popup)
    frame_scroll.pack(fill="both", expand=True, padx=10, pady=5)
    
    # Dicionário para armazenar estados booleanos simples
    checkboxes_state = {}
    
    def atualizar_contador():
        count = sum(1 for v in checkboxes_state.values() if v.get())
        lbl_count.configure(text=f"Selecionados: {count}/4")
    
    for canal in canais_possiveis:
        is_selected = canal in app_instance.selected_live_channels
        var = tk.BooleanVar(value=is_selected)
        checkboxes_state[canal] = var
        
        chk = ctk.CTkCheckBox(
            frame_scroll, 
            text=canal, 
            variable=var,
            command=atualizar_contador
        )
        chk.pack(anchor="w", pady=2)

    def confirmar_selecao():
        novos_selecionados = [canal for canal, var in checkboxes_state.items() if var.get()]
        
        if len(novos_selecionados) > 4:
            messagebox.showwarning("Muitos Canais", "Selecione no máximo 4 canais para não poluir o gráfico.")
            return
        
        if len(novos_selecionados) == 0:
            messagebox.showwarning("Nenhum Canal", "Selecione pelo menos 1 canal.")
            return
            
        app_instance.selected_live_channels = novos_selecionados[:]
        print(f"[DEBUG] Canais selecionados: {app_instance.selected_live_channels}")
        
        # Reconfigura o gráfico
        update_live_plot_style(app_instance)
        popup.destroy()

    ctk.CTkButton(popup, text="Confirmar", command=confirmar_selecao, 
                  fg_color=COLOR_ACCENT_GOLD, text_color="black").pack(pady=10)
