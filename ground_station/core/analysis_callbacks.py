"""
Módulo de callbacks de análise para a aplicação PUCPR Racing.
Contém todas as funções avançadas de análise de telemetria.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import numpy as np
import re
from config_manager import get_channel_name
from calculations import calcular_metricas_aceleracao, calcular_tempos_volta
from core.constants import (
    COLOR_ACCENT_RED, COLOR_ACCENT_GOLD, COLOR_ACCENT_CYAN, COLOR_ACCENT_GREEN,
    COLOR_BG_TERTIARY, COLOR_BORDER
)


# ==============================================================================
# TAB GERAL/PLOTAGEM - FUNÇÕES DE ANÁLISE
# ==============================================================================

def mostrar_estatisticas_canais(app_instance):
    """Mostra estatísticas descritivas dos canais selecionados."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    canais_selecionados = app_instance.obter_canais_selecionados()
    if not canais_selecionados:
        return messagebox.showwarning("Aviso", "Selecione pelo menos 1 canal.")
    
    stats_text = "=== ESTATÍSTICAS DOS CANAIS ===\n\n"
    for canal in canais_selecionados:
        if canal not in app_instance.data_frame.columns:
            continue
        data = app_instance.data_frame[canal].dropna()
        stats_text += f"📊 {canal}:\n"
        stats_text += f"   Média: {data.mean():.4f}\n"
        stats_text += f"   Mediana: {data.median():.4f}\n"
        stats_text += f"   Desvio Padrão: {data.std():.4f}\n"
        stats_text += f"   Mín: {data.min():.4f} | Máx: {data.max():.4f}\n"
        stats_text += f"   Amplitude: {data.max() - data.min():.4f}\n\n"
    
    # Mostra em janela de diálogo
    top = ctk.CTkToplevel(app_instance)
    top.title("Estatísticas dos Canais")
    top.geometry("500x600")
    txt = ctk.CTkTextbox(top, wrap="word", font=ctk.CTkFont(family="Consolas", size=11))
    txt.pack(fill="both", expand=True, padx=10, pady=10)
    txt.insert("1.0", stats_text)
    txt.configure(state="disabled")
    app_instance.atualizar_status("Estatísticas calculadas.")


def comparar_voltas_gui(app_instance):
    """Abre janela para comparar canais entre duas voltas específicas."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    if app_instance.lap_numbers_series is None or 'LapNumber' not in app_instance.data_frame.columns:
        return messagebox.showwarning("Aviso", "Calcule as voltas primeiro.")
    
    voltas_unicas = sorted(app_instance.data_frame['LapNumber'].dropna().unique())
    if len(voltas_unicas) < 2:
        return messagebox.showwarning("Aviso", "Precisa de pelo menos 2 voltas completas.")
    
    # Diálogo de seleção
    dialog = ctk.CTkToplevel(app_instance)
    dialog.title("Comparar Voltas")
    dialog.geometry("400x250")
    
    ctk.CTkLabel(dialog, text="Selecione duas voltas para comparar:", 
                 font=app_instance.LARGE_FONT_BOLD).pack(pady=15)
    
    ctk.CTkLabel(dialog, text="Volta 1:", font=app_instance.DEFAULT_FONT).pack(pady=5)
    var_lap1 = ctk.IntVar(value=int(voltas_unicas[0]))
    combo1 = ctk.CTkComboBox(dialog, values=[str(int(v)) for v in voltas_unicas], 
                             variable=var_lap1, width=200)
    combo1.pack(pady=5)
    
    ctk.CTkLabel(dialog, text="Volta 2:", font=app_instance.DEFAULT_FONT).pack(pady=5)
    var_lap2 = ctk.IntVar(value=int(voltas_unicas[-1]) if len(voltas_unicas) > 1 else int(voltas_unicas[0]))
    combo2 = ctk.CTkComboBox(dialog, values=[str(int(v)) for v in voltas_unicas], 
                             variable=var_lap2, width=200)
    combo2.pack(pady=5)
    
    def executar_comparacao():
        lap1, lap2 = var_lap1.get(), var_lap2.get()
        if lap1 == lap2:
            return messagebox.showwarning("Aviso", "Selecione voltas diferentes.")
        dialog.destroy()
        _plotar_comparacao_voltas(app_instance, lap1, lap2)
    
    ctk.CTkButton(dialog, text="Comparar", command=executar_comparacao, 
                  fg_color=COLOR_ACCENT_RED).pack(pady=15)


def _plotar_comparacao_voltas(app_instance, lap1, lap2):
    """Plota comparação de canais selecionados entre duas voltas."""
    canais = app_instance.obter_canais_selecionados()
    if not canais:
        return messagebox.showwarning("Aviso", "Selecione pelo menos 1 canal.")
    
    df1 = app_instance.data_frame[app_instance.data_frame['LapNumber'] == lap1]
    df2 = app_instance.data_frame[app_instance.data_frame['LapNumber'] == lap2]
    
    app_instance.eixo_plot.clear()
    time_col = get_channel_name(app_instance.channel_mapping, 'timestamp', 
                                 app_instance.data_frame.columns)
    
    for canal in canais[:4]:  # Limita a 4 canais
        if canal in df1.columns and canal in df2.columns:
            if time_col and time_col in df1.columns:
                t1 = (df1[time_col] - df1[time_col].iloc[0]).values
                t2 = (df2[time_col] - df2[time_col].iloc[0]).values
            else:
                t1, t2 = range(len(df1)), range(len(df2))
            
            app_instance.eixo_plot.plot(t1, df1[canal].values, 
                                       label=f"{canal} (Volta {lap1})", 
                                       linestyle='-', linewidth=1.5)
            app_instance.eixo_plot.plot(t2, df2[canal].values, 
                                       label=f"{canal} (Volta {lap2})", 
                                       linestyle='--', linewidth=1.5)
    
    app_instance.eixo_plot.set_xlabel("Tempo (s)")
    app_instance.eixo_plot.set_ylabel("Valor")
    app_instance.eixo_plot.set_title(f"Comparação: Volta {lap1} vs Volta {lap2}")
    app_instance.eixo_plot.legend(fontsize=8, loc='best')
    app_instance.eixo_plot.grid(True, alpha=0.3)
    app_instance.canvas_plot.draw()
    app_instance.atualizar_status(f"Comparação entre voltas {lap1} e {lap2} plotada.")


def exportar_plot_atual(app_instance):
    """Exporta o gráfico atual como imagem PNG de alta qualidade."""
    filepath = filedialog.asksaveasfilename(
        title="Exportar Gráfico", 
        defaultextension=".png", 
        filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")]
    )
    if filepath:
        try:
            app_instance.figura_plot.savefig(filepath, dpi=300, bbox_inches='tight', 
                                            facecolor=COLOR_BG_TERTIARY)
            messagebox.showinfo("Sucesso", f"Gráfico exportado para:\n{filepath}")
            app_instance.atualizar_status("Gráfico exportado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar: {e}")


# ==============================================================================
# TAB SKID PAD - FUNÇÕES DE ANÁLISE
# ==============================================================================

def analisar_skidpad_completo(app_instance):
    """Análise completa do Skid Pad com detecção de fases e métricas avançadas."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    app_instance.atualizar_status("Calculando análise completa Skid Pad...")
    
    lat_col = get_channel_name(app_instance.channel_mapping, 'lataccel', 
                                app_instance.data_frame.columns)
    lon_col = get_channel_name(app_instance.channel_mapping, 'longaccel', 
                                app_instance.data_frame.columns)
    speed_col = get_channel_name(app_instance.channel_mapping, 'vehiclespeed', 
                                  app_instance.data_frame.columns)
    
    resultados = "=== ANÁLISE COMPLETA SKID PAD ===\n\n"
    
    if lat_col and lat_col in app_instance.data_frame.columns:
        lat_data = app_instance.data_frame[lat_col].abs()
        resultados += f"📊 G LATERAL:\n"
        resultados += f"   Máximo: {lat_data.max():.4f} G\n"
        resultados += f"   Média: {lat_data.mean():.4f} G\n"
        resultados += f"   Médio (Top 10%): {lat_data.nlargest(int(len(lat_data)*0.1)).mean():.4f} G\n"
        resultados += f"   Desvio Padrão: {lat_data.std():.4f} G\n\n"
        
        # Análise de consistência
        rolling_mean = lat_data.rolling(window=50, center=True).mean()
        consistency = 1 - (lat_data.std() / lat_data.mean()) if lat_data.mean() > 0 else 0
        resultados += f"🎯 CONSISTÊNCIA: {consistency*100:.2f}%\n\n"
    
    if speed_col and speed_col in app_instance.data_frame.columns:
        speed_data = app_instance.data_frame[speed_col]
        resultados += f"🏎️ VELOCIDADE:\n"
        resultados += f"   Média: {speed_data.mean():.2f} km/h\n"
        resultados += f"   Mínima: {speed_data.min():.2f} km/h\n"
        resultados += f"   Máxima: {speed_data.max():.2f} km/h\n\n"
    
    if (lat_col and speed_col and 
        lat_col in app_instance.data_frame.columns and 
        speed_col in app_instance.data_frame.columns):
        # Estimativa de raio (r = v² / (g_lat * 9.81))
        velocidade_ms = app_instance.data_frame[speed_col] / 3.6
        g_lat = app_instance.data_frame[lat_col].abs()
        raio_estimado = (velocidade_ms ** 2) / (g_lat * 9.81 + 0.001)  # Evita divisão por zero
        raio_medio = raio_estimado.median()
        resultados += f"📐 RAIO ESTIMADO (mediana): {raio_medio:.2f} m\n"
    
    app_instance.atualizar_texto_resultado("Skid_Pad", resultados)
    app_instance.atualizar_status("Análise completa Skid Pad concluída.")


def plotar_consistencia_skidpad(app_instance):
    """Plota gráfico de consistência do G lateral ao longo do tempo."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    lat_col = get_channel_name(app_instance.channel_mapping, 'lataccel', 
                                app_instance.data_frame.columns)
    if not lat_col:
        return messagebox.showwarning("Aviso", "Canal LatAccel não encontrado.")
    
    app_instance.eixo_plot.clear()
    lat_data = app_instance.data_frame[lat_col].abs()
    rolling_mean = lat_data.rolling(window=50, center=True).mean()
    rolling_std = lat_data.rolling(window=50, center=True).std()
    
    time_col = get_channel_name(app_instance.channel_mapping, 'timestamp', 
                                 app_instance.data_frame.columns)
    if time_col and time_col in app_instance.data_frame.columns:
        time_data = (app_instance.data_frame[time_col] - 
                     app_instance.data_frame[time_col].iloc[0]).values
    else:
        time_data = range(len(lat_data))
    
    app_instance.eixo_plot.plot(time_data, lat_data, label='G Lateral (abs)', 
                                alpha=0.3, linewidth=0.5)
    app_instance.eixo_plot.plot(time_data, rolling_mean, label='Média Móvel (50pts)', 
                                color=COLOR_ACCENT_RED, linewidth=2)
    app_instance.eixo_plot.fill_between(time_data, rolling_mean - rolling_std, 
                                        rolling_mean + rolling_std, 
                                        alpha=0.2, color=COLOR_ACCENT_GOLD, 
                                        label='± 1 Desvio Padrão')
    
    app_instance.eixo_plot.set_xlabel("Tempo (s)")
    app_instance.eixo_plot.set_ylabel("G Lateral (abs)")
    app_instance.eixo_plot.set_title("Consistência de G Lateral - Skid Pad")
    app_instance.eixo_plot.legend()
    app_instance.eixo_plot.grid(True, alpha=0.3)
    app_instance.canvas_plot.draw()
    app_instance.atualizar_status("Gráfico de consistência plotado.")


def detectar_secoes_skidpad(app_instance):
    """Detecta automaticamente seções esquerda/direita do Skid Pad."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    lat_col = get_channel_name(app_instance.channel_mapping, 'lataccel', 
                                app_instance.data_frame.columns)
    if not lat_col:
        return messagebox.showwarning("Aviso", "Canal LatAccel não encontrado.")
    
    lat_data = app_instance.data_frame[lat_col]
    # Detecção simples: positivo = direita, negativo = esquerda
    secao_direita = lat_data > 0.5
    secao_esquerda = lat_data < -0.5
    
    n_direita = secao_direita.sum()
    n_esquerda = secao_esquerda.sum()
    
    g_max_direita = lat_data[secao_direita].max() if n_direita > 0 else 0
    g_max_esquerda = lat_data[secao_esquerda].min() if n_esquerda > 0 else 0
    
    resultado = f"=== DETECÇÃO AUTOMÁTICA DE SEÇÕES ===\n\n"
    resultado += f"🔵 CURVA DIREITA (G > 0.5):\n"
    resultado += f"   Pontos: {n_direita}\n"
    resultado += f"   G Lateral Máx: {g_max_direita:.4f} G\n\n"
    resultado += f"🔴 CURVA ESQUERDA (G < -0.5):\n"
    resultado += f"   Pontos: {n_esquerda}\n"
    resultado += f"   G Lateral Mín: {g_max_esquerda:.4f} G\n\n"
    resultado += f"⚖️ SIMETRIA: {(min(n_direita, n_esquerda) / max(n_direita, n_esquerda) * 100):.1f}%\n"
    
    app_instance.atualizar_texto_resultado("Skid_Pad", resultado)
    app_instance.atualizar_status("Seções detectadas automaticamente.")


# ==============================================================================
# TAB ACELERAÇÃO - FUNÇÕES DE ANÁLISE
# ==============================================================================

def analisar_aceleracao_completo(app_instance):
    """Análise de aceleração em múltiplas distâncias (0-25m, 0-50m, 0-75m, 0-100m)."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    app_instance.atualizar_status("Calculando análise multi-distância...")
    
    distancias = [25, 50, 75, 100]
    resultado = "=== ANÁLISE DE ACELERAÇÃO MULTI-DISTÂNCIA ===\n\n"
    
    for dist in distancias:
        metricas = calcular_metricas_aceleracao(app_instance.data_frame, 
                                                app_instance.channel_mapping, 
                                                distance_target=dist)
        resultado += f"📏 0-{dist}m:\n{metricas}\n{'='*40}\n\n"
    
    app_instance.atualizar_texto_resultado("Aceleração", resultado)
    app_instance.atualizar_status("Análise multi-distância concluída.")


def plotar_comparativo_aceleracao(app_instance):
    """Plota gráfico comparativo de tempos em diferentes distâncias."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    # Extrai valores dos cálculos (simplificado - em produção, guardaria os resultados)
    distancias = [25, 50, 75, 100]
    tempos = []
    
    for dist in distancias:
        metricas_str = calcular_metricas_aceleracao(app_instance.data_frame, 
                                                     app_instance.channel_mapping, 
                                                     distance_target=dist)
        # Parse simples do resultado (busca linha "Tempo:" e extrai valor)
        match = re.search(r'Tempo.*?([\d.]+)\s*s', metricas_str)
        if match:
            tempos.append(float(match.group(1)))
        else:
            tempos.append(0)
    
    app_instance.eixo_plot.clear()
    app_instance.eixo_plot.bar(distancias, tempos, color=COLOR_ACCENT_RED, 
                               edgecolor=COLOR_BORDER, linewidth=1.5)
    app_instance.eixo_plot.set_xlabel("Distância (m)")
    app_instance.eixo_plot.set_ylabel("Tempo (s)")
    app_instance.eixo_plot.set_title("Comparativo de Aceleração por Distância")
    
    for i, (d, t) in enumerate(zip(distancias, tempos)):
        if t > 0:
            app_instance.eixo_plot.text(d, t + 0.1, f"{t:.2f}s", ha='center', 
                                       fontsize=10, fontweight='bold')
    
    app_instance.eixo_plot.grid(True, axis='y', alpha=0.3)
    app_instance.canvas_plot.draw()
    app_instance.atualizar_status("Comparativo de aceleração plotado.")


def plotar_gforce_aceleracao(app_instance):
    """Plota análise de G-Force durante aceleração."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    lon_col = get_channel_name(app_instance.channel_mapping, 'longaccel', 
                                app_instance.data_frame.columns)
    if not lon_col:
        return messagebox.showwarning("Aviso", "Canal LongAccel não encontrado.")
    
    app_instance.eixo_plot.clear()
    time_col = get_channel_name(app_instance.channel_mapping, 'timestamp', 
                                 app_instance.data_frame.columns)
    
    if time_col and time_col in app_instance.data_frame.columns:
        time_data = (app_instance.data_frame[time_col] - 
                     app_instance.data_frame[time_col].iloc[0]).values
    else:
        time_data = range(len(app_instance.data_frame))
    
    lon_data = app_instance.data_frame[lon_col]
    
    app_instance.eixo_plot.plot(time_data, lon_data, color=COLOR_ACCENT_GOLD, linewidth=1.5)
    app_instance.eixo_plot.axhline(y=0, color=COLOR_BORDER, linestyle='--', linewidth=1)
    app_instance.eixo_plot.fill_between(time_data, lon_data, 0, where=(lon_data > 0), 
                                        alpha=0.3, color=COLOR_ACCENT_GREEN, 
                                        label='Aceleração')
    app_instance.eixo_plot.fill_between(time_data, lon_data, 0, where=(lon_data < 0), 
                                        alpha=0.3, color=COLOR_ACCENT_RED, 
                                        label='Frenagem')
    
    app_instance.eixo_plot.set_xlabel("Tempo (s)")
    app_instance.eixo_plot.set_ylabel("G Longitudinal")
    app_instance.eixo_plot.set_title("Análise de G-Force Longitudinal")
    app_instance.eixo_plot.legend()
    app_instance.eixo_plot.grid(True, alpha=0.3)
    app_instance.canvas_plot.draw()
    app_instance.atualizar_status("G-Force longitudinal plotado.")


# ==============================================================================
# TAB AUTOCROSS/ENDURANCE - FUNÇÕES DE ANÁLISE
# ==============================================================================

def analisar_tempos_volta_completo(app_instance):
    """Análise expandida de voltas com estatísticas detalhadas."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    app_instance.atualizar_status("Calculando análise completa de voltas...")
    
    lap_numbers, resultados_base = calcular_tempos_volta(
        app_instance.data_frame, 
        app_instance.channel_mapping, 
        app_instance.track_config, 
        app_instance.analysis_config
    )
    
    # Expande com estatísticas adicionais
    if lap_numbers is not None and len(lap_numbers.unique()) > 1:
        app_instance.lap_numbers_series = lap_numbers
        if 'LapNumber' not in app_instance.data_frame.columns:
            app_instance.data_frame.insert(0, 'LapNumber', lap_numbers)
            app_instance.atualizar_lista_canais()
        
        # Calcula tempos de cada volta
        voltas = sorted(lap_numbers.dropna().unique())
        tempos_voltas = []
        time_col = get_channel_name(app_instance.channel_mapping, 'timestamp', 
                                     app_instance.data_frame.columns)
        
        if time_col and time_col in app_instance.data_frame.columns:
            for volta in voltas:
                dados_volta = app_instance.data_frame[app_instance.data_frame['LapNumber'] == volta]
                if len(dados_volta) > 0:
                    tempo_volta = (dados_volta[time_col].iloc[-1] - 
                                  dados_volta[time_col].iloc[0])
                    tempos_voltas.append(tempo_volta)
            
            resultados_base += f"\n{'='*50}\n"
            resultados_base += f"📊 ESTATÍSTICAS DAS VOLTAS:\n"
            resultados_base += f"   Total de voltas: {len(tempos_voltas)}\n"
            if len(tempos_voltas) > 0:
                resultados_base += f"   Tempo médio: {np.mean(tempos_voltas):.3f} s\n"
                resultados_base += f"   Melhor volta: {min(tempos_voltas):.3f} s\n"
                resultados_base += f"   Pior volta: {max(tempos_voltas):.3f} s\n"
                resultados_base += f"   Desvio padrão: {np.std(tempos_voltas):.3f} s\n"
                resultados_base += f"   Consistência: {(1 - np.std(tempos_voltas)/np.mean(tempos_voltas))*100:.1f}%\n"
    
    app_instance.atualizar_texto_resultado("Autocross_Endurance", resultados_base)
    app_instance.atualizar_status("Análise completa de voltas concluída.")


def analisar_setores_pista(app_instance):
    """Divide a pista em setores e analisa performance por setor."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    if app_instance.lap_numbers_series is None:
        return messagebox.showwarning("Aviso", "Calcule as voltas primeiro.")
    
    # Divide cada volta em 3 setores (33%, 66%, 100%)
    resultado = "=== ANÁLISE POR SETORES ===\n\n"
    voltas = sorted(app_instance.data_frame['LapNumber'].dropna().unique())
    
    for volta in voltas[:5]:  # Analisa primeiras 5 voltas
        dados_volta = app_instance.data_frame[app_instance.data_frame['LapNumber'] == volta]
        n_points = len(dados_volta)
        
        setor1 = dados_volta.iloc[:n_points//3]
        setor2 = dados_volta.iloc[n_points//3:2*n_points//3]
        setor3 = dados_volta.iloc[2*n_points//3:]
        
        speed_col = get_channel_name(app_instance.channel_mapping, 'vehiclespeed', 
                                      dados_volta.columns)
        if speed_col:
            resultado += f"🏁 VOLTA {int(volta)}:\n"
            resultado += f"   Setor 1: Vel Média = {setor1[speed_col].mean():.1f} km/h\n"
            resultado += f"   Setor 2: Vel Média = {setor2[speed_col].mean():.1f} km/h\n"
            resultado += f"   Setor 3: Vel Média = {setor3[speed_col].mean():.1f} km/h\n\n"
    
    app_instance.atualizar_texto_resultado("Autocross_Endurance", resultado)
    app_instance.atualizar_status("Análise por setores concluída.")


def plotar_heatmap_performance(app_instance):
    """Plota heatmap de performance ao longo das voltas."""
    if app_instance.data_frame is None:
        return messagebox.showwarning("Aviso", "Carregue um log primeiro.")
    
    if app_instance.lap_numbers_series is None:
        return messagebox.showwarning("Aviso", "Calcule as voltas primeiro.")
    
    speed_col = get_channel_name(app_instance.channel_mapping, 'vehiclespeed', 
                                  app_instance.data_frame.columns)
    if not speed_col:
        return messagebox.showwarning("Aviso", "Canal de velocidade não encontrado.")
    
    voltas = sorted(app_instance.data_frame['LapNumber'].dropna().unique())
    if len(voltas) < 2:
        return messagebox.showwarning("Aviso", "Precisa de pelo menos 2 voltas.")
    
    # Cria matriz de velocidades (voltas x pontos normalizados)
    n_pontos = 100  # Normaliza todas as voltas para 100 pontos
    matriz_velocidades = []
    
    for volta in voltas[:10]:  # Limita a 10 voltas para visualização
        dados_volta = app_instance.data_frame[app_instance.data_frame['LapNumber'] == volta]
        velocidades = dados_volta[speed_col].values
        
        # Interpola para n_pontos fixo (método simples se scipy não disponível)
        try:
            from scipy.interpolate import interp1d
            x_original = np.linspace(0, 1, len(velocidades))
            x_novo = np.linspace(0, 1, n_pontos)
            f = interp1d(x_original, velocidades, kind='linear', fill_value='extrapolate')
            velocidades_interp = f(x_novo)
        except ImportError:
            # Fallback: resample simples usando numpy
            velocidades_interp = np.interp(np.linspace(0, len(velocidades)-1, n_pontos), 
                                           np.arange(len(velocidades)), velocidades)
        matriz_velocidades.append(velocidades_interp)
    
    app_instance.eixo_plot.clear()
    im = app_instance.eixo_plot.imshow(matriz_velocidades, aspect='auto', 
                                       cmap='RdYlGn', interpolation='bilinear')
    app_instance.eixo_plot.set_xlabel("Posição na Volta (%)")
    app_instance.eixo_plot.set_ylabel("Número da Volta")
    app_instance.eixo_plot.set_title("Heatmap de Velocidade por Volta")
    app_instance.eixo_plot.set_yticks(range(len(matriz_velocidades)))
    app_instance.eixo_plot.set_yticklabels([f"V{int(v)}" for v in voltas[:len(matriz_velocidades)]])
    
    app_instance.figura_plot.colorbar(im, ax=app_instance.eixo_plot, label='Velocidade (km/h)')
    app_instance.canvas_plot.draw()
    app_instance.atualizar_status("Heatmap de performance plotado.")


def comparar_voltas_detalhado(app_instance):
    """Comparação detalhada entre voltas com overlay de múltiplos canais."""
    comparar_voltas_gui(app_instance)  # Reutiliza a função já existente
