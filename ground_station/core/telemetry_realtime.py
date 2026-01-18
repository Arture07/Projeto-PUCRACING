"""
Módulo de Telemetria em Tempo Real - PUCPR Racing

Responsável por:
- Thread de leitura CAN via UDP multicast
- Decodificação de mensagens usando DBC
- Gerenciamento de dados ao vivo (armazenamento + fila)
- Atualização da GUI (gráficos + dashboards)
"""

import time
import threading
import queue
import platform
import os
try:
    import can
    import cantools
except ImportError:
    can = None
    cantools = None
    print("Aviso: python-can e/ou cantools não instalados. Telemetria CAN desabilitada.")

from core.constants import (
    COLOR_ACCENT_RED, COLOR_ACCENT_GOLD, 
    COLOR_ACCENT_GREEN, COLOR_ACCENT_CYAN
)


def toggle_live_telemetry(app_instance):
    """Alterna entre iniciar e parar a telemetria ao vivo."""
    if not app_instance.is_live_active:
        start_live_telemetry(app_instance)
    else:
        stop_live_telemetry(app_instance)


def start_live_telemetry(app_instance):
    """Inicia a thread de leitura CAN."""
    app_instance.is_live_active = True
    app_instance.stop_live_event.clear()
    
    # Inicia dicionário de armazenamento
    app_instance.live_data_storage = {'Time': []}
    
    app_instance.start_time_live = time.time()
    
    # Configura gráfico inicial
    app_instance.update_live_plot_style()
    
    app_instance.btn_live_toggle.configure(text="⏹️ Parar Telemetria", fg_color="#C62828") 
    app_instance.lbl_live_status.configure(text="Status: Conectado (Aguardando dados UDP 239.0.0.1...)")
    
    app_instance.live_thread = threading.Thread(target=loop_leitura_can, args=(app_instance,), daemon=True)
    app_instance.live_thread.start()
    
    app_instance.after(100, lambda: update_live_gui(app_instance))


def stop_live_telemetry(app_instance):
    """Para a thread de leitura CAN."""
    app_instance.is_live_active = False
    app_instance.stop_live_event.set()
    app_instance.btn_live_toggle.configure(text="▶️ Iniciar Telemetria", fg_color=COLOR_ACCENT_RED)
    app_instance.lbl_live_status.configure(text="Status: Parado")


def loop_leitura_can(app_instance):
    """Loop rodando em thread separada para ler CAN Bus."""
    if can is None or cantools is None:
        print("Erro: python-can/cantools não disponíveis. Thread CAN não iniciada.")
        return
    
    db = None
    try:
        # Tenta carregar DBC (pasta config)
        dbc_path = '../config/pucpr.dbc'
        if os.path.exists(dbc_path):
            db = cantools.database.load_file(dbc_path)
        else:
            print("Aviso: pucpr.dbc não encontrado. Tentando ler raw.")
    except Exception as e:
        print(f"Erro ao carregar DBC na thread: {e}")

    bus = None
    try:
        # Configuração Windows (UDP Multicast) - Igual ao simulator_carro.py / central.py
        # Se for Linux/Rpi seria 'socketcan'
        if platform.system() == "Windows":
            bus = can.interface.Bus(channel='239.0.0.1', interface='udp_multicast')
        else: 
            # Fallback ou configuração linux (não testado aqui)
            bus = can.interface.Bus(channel='can0', bustype='socketcan')

        print("Thread CAN iniciada.")
        while not app_instance.stop_live_event.is_set():
            # Recebe com timeout para poder verificar o evento de parada
            msg = bus.recv(0.5) 
            if msg:
                try:
                    if db:
                        dados = db.decode_message(msg.arbitration_id, msg.data)
                        app_instance.live_queue.put(dados)
                        # print(f"Dados CAN recebidos: {dados}") # Debug
                    else:
                        # Se não tem DBC, tenta algo genérico ou ignora
                        pass
                except Exception as e_decode:
                    # print(f"Erro decode: {e_decode}")
                    pass
    except Exception as e:
        print(f"Erro na conexão CAN: {e}")
        # Pode-se enviar mensagem para GUI via queue de status se quiser
        app_instance.stop_live_event.set()
    finally:
        if bus:
            bus.shutdown()
        print("Thread CAN finalizada.")


def update_live_gui(app_instance):
    """Atualiza os labels da GUI consumindo a fila."""
    if not app_instance.is_live_active:
        return

    try:
        # Processa tudo que está na fila (esvazia para pegar o mais recente)
        dados_recentes = {}
        pacotes_processados = 0
        try:
            while not app_instance.live_queue.empty():
                d = app_instance.live_queue.get_nowait()
                dados_recentes.update(d)
                pacotes_processados += 1
        except queue.Empty:
            pass
        
        if pacotes_processados > 0:
            app_instance.lbl_live_status.configure(text="Status: Recebendo dados...")

            # Se usuário estiver usando Pan/Zoom da toolbar, não force auto-scroll
            try:
                toolbar_mode = getattr(app_instance.toolbar_live, 'mode', '') if hasattr(app_instance, 'toolbar_live') else ''
                if toolbar_mode and app_instance.auto_scroll:
                    app_instance.auto_scroll = False
                    if hasattr(app_instance, 'switch_auto_scroll'):
                        app_instance.switch_auto_scroll.deselect()

                    # Abre o eixo X para facilitar navegar no histórico
                    t_data = app_instance.live_data_storage.get('Time', [])
                    if t_data and len(t_data) >= 2:
                        app_instance.ax_live.set_xlim(0, t_data[-1])
            except Exception:
                pass

            # Atualiza indicador de Hz (com base no tempo relativo)
            current_time_rel = time.time() - app_instance.start_time_live
            try:
                app_instance._live_hz_times.append(current_time_rel)
                if len(app_instance._live_hz_times) >= 2:
                    dt = app_instance._live_hz_times[-1] - app_instance._live_hz_times[0]
                    hz = (len(app_instance._live_hz_times) - 1) / dt if dt > 1e-6 else 0.0
                    app_instance.lbl_live_hz.configure(text=f"Hz: {hz:0.1f}")
            except Exception:
                pass

        # --- ATUALIZAÇÃO DO GRÁFICO E ARMAZENAMENTO ---
        # Sincronização robusta de dados para prevenir erros de dimensão (numpy shape mismatch)
        current_time_rel = time.time() - app_instance.start_time_live
        
        if pacotes_processados > 0:
            # 1. Atualiza o Tempo
            if 'Time' not in app_instance.live_data_storage: 
                app_instance.live_data_storage['Time'] = []
            app_instance.live_data_storage['Time'].append(current_time_rel)
            
            target_len = len(app_instance.live_data_storage['Time'])
            
            # 2. Identifica todos os canais que precisamos rastrear
            # (Os que já temos + os que chegaram agora + os que o usuário quer ver)
            canais_para_atualizar = set(app_instance.live_data_storage.keys()) | set(dados_recentes.keys()) | set(app_instance.selected_live_channels)
            canais_para_atualizar.discard('Time') # Remove Time da lista de canais de dados

            for canal in canais_para_atualizar:
                if canal not in app_instance.live_data_storage:
                    app_instance.live_data_storage[canal] = []
                
                # 3. Padding (Preenchimento): Garante que o histórico existe (com zeros) se o canal é novo
                current_len = len(app_instance.live_data_storage[canal])
                missing_steps = target_len - 1 - current_len
                
                if missing_steps > 0:
                    # Preenche lacunas com 0 
                    app_instance.live_data_storage[canal].extend([0] * missing_steps)

                # 4. Adiciona o valor atual
                valor = dados_recentes.get(canal)
                if valor is None:
                    # Hold Last Value (Manter anterior) ou 0 se não tiver anterior
                    if len(app_instance.live_data_storage[canal]) > 0:
                        valor = app_instance.live_data_storage[canal][-1]
                    else:
                        valor = 0
                app_instance.live_data_storage[canal].append(valor)

            # --- PLOTAGEM DE PERFORMANCE (SLICING) ---
            # Se estiver congelado, não redesenha (mas continua armazenando dados)
            if not app_instance.live_freeze:
                t_data_full = app_instance.live_data_storage['Time']
                start_idx = 0
                
                # Otimização: Se tiver muitos pontos e Auto-Scroll ligado, plota apenas a janela visível + margem
                if app_instance.auto_scroll and len(t_data_full) > 300:
                    window_secs = 12.0 # Janela de 10s + margem
                    last_time = t_data_full[-1]
                    target_time = last_time - window_secs
                    for i in range(len(t_data_full)-1, -1, -1):
                        if t_data_full[i] < target_time:
                            start_idx = i
                            break

                t_data_plot = t_data_full[start_idx:]

                if app_instance.switch_normalize.get() == 1:
                    for canal in app_instance.selected_live_channels:
                        if canal in app_instance.live_data_storage and canal in app_instance.live_lines:
                            line = app_instance.live_lines[canal]
                            y_data_full = app_instance.live_data_storage[canal]
                            if len(t_data_full) == len(y_data_full):
                                line.set_data(t_data_plot, y_data_full[start_idx:])
                                if canal in app_instance.live_axes:
                                    ax = app_instance.live_axes[canal]
                                    ax.relim(); ax.autoscale_view(scalex=False, scaley=True)
                                else:
                                    app_instance.ax_live.relim(); app_instance.ax_live.autoscale_view(scalex=False, scaley=True)
                else:
                    for canal, line in app_instance.live_lines.items():
                        if canal in app_instance.live_data_storage:
                            y_data_full = app_instance.live_data_storage[canal]
                            if len(t_data_full) == len(y_data_full):
                                line.set_data(t_data_plot, y_data_full[start_idx:])

                    app_instance.ax_live.relim()
                    app_instance.ax_live.autoscale_view(scalex=False, scaley=True)
                
                # Não sobrescreve o eixo X se o usuário estiver navegando (pan/zoom)
                try:
                    toolbar_mode = getattr(app_instance.toolbar_live, 'mode', '') if hasattr(app_instance, 'toolbar_live') else ''
                except Exception:
                    toolbar_mode = ''

                if app_instance.auto_scroll and not toolbar_mode:
                    window_size = 10.0
                    if current_time_rel > window_size:
                        app_instance.ax_live.set_xlim(current_time_rel - window_size, current_time_rel)
                    else:
                        app_instance.ax_live.set_xlim(0, max(current_time_rel, window_size))
                
                app_instance.canvas_live.draw_idle()

        # Atualiza labels e dashboard
        _update_dashboard_labels(app_instance, dados_recentes)
    
    except Exception as e:
        print(f"Erro no update_live_gui (Recuperado): {e}")

    # Reagendar a si mesmo com taxa menor (10 FPS) para economizar CPU
    if app_instance.is_live_active:
        app_instance.after(100, lambda: update_live_gui(app_instance))


def _update_dashboard_labels(app_instance, dados_recentes):
    """Atualiza labels dos dashboards com os dados mais recentes."""
    
    # Motor/ECU
    if 'RPM' in dados_recentes:
        txt = f"{dados_recentes['RPM']:.0f}"
        app_instance.lbl_val_rpm.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_rpm'): 
            app_instance.lbl_dash_rpm.configure(text=txt)
        # Atualiza barra de progresso (RPM max ~13000)
        if hasattr(app_instance, 'prog_dash_rpm'):
            rpm_val = dados_recentes['RPM']
            rpm_normalized = min(rpm_val / 13000.0, 1.0)
            app_instance.prog_dash_rpm.set(rpm_normalized)
            # Cor dinâmica: verde <8000, amarelo 8000-11000, vermelho >11000
            if rpm_val < 8000:
                app_instance.prog_dash_rpm.configure(progress_color=COLOR_ACCENT_GREEN)
            elif rpm_val < 11000:
                app_instance.prog_dash_rpm.configure(progress_color=COLOR_ACCENT_GOLD)
            else:
                app_instance.prog_dash_rpm.configure(progress_color=COLOR_ACCENT_RED)

    if 'Temperatura' in dados_recentes:
        txt = f"{dados_recentes['Temperatura']:.0f}"
        app_instance.lbl_val_temp.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_temp'): 
            app_instance.lbl_dash_temp.configure(text=txt)

    if 'ThrottlePos' in dados_recentes:
        tps_val = dados_recentes['ThrottlePos']
        txt = f"{tps_val:.0f}%"
        app_instance.lbl_val_tps.configure(text=txt.replace('%', ''))
        if hasattr(app_instance, 'lbl_dash_tps'): 
            app_instance.lbl_dash_tps.configure(text=txt)
        # Atualiza barra de progresso TPS (0-100%)
        if hasattr(app_instance, 'prog_dash_tps'):
            app_instance.prog_dash_tps.set(min(tps_val / 100.0, 1.0))

    if 'Lambda' in dados_recentes:
        txt = f"{dados_recentes['Lambda']:.2f}"
        app_instance.lbl_val_lambda.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_lambda'): 
            app_instance.lbl_dash_lambda.configure(text=txt)

    # Pilotagem / IMU
    if 'SteeringAngle' in dados_recentes:
        txt = f"{dados_recentes['SteeringAngle']:.1f}"
        app_instance.lbl_val_steer.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_steer'): 
            app_instance.lbl_dash_steer.configure(text=txt)

    if 'BrakePressure' in dados_recentes:
        brake_val = dados_recentes['BrakePressure']
        txt = f"{brake_val:.0f}"
        app_instance.lbl_val_brake.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_brake'): 
            app_instance.lbl_dash_brake.configure(text=txt)
        # Atualiza barra de progresso Brake (max ~200 bar)
        if hasattr(app_instance, 'prog_dash_brake'):
            brake_normalized = min(brake_val / 200.0, 1.0)
            app_instance.prog_dash_brake.set(brake_normalized)

    if 'AccelX' in dados_recentes:
        txt = f"{dados_recentes['AccelX']:.2f}"
        app_instance.lbl_val_accel_x.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_accel_x'): 
            app_instance.lbl_dash_accel_x.configure(text=txt)

    if 'AccelY' in dados_recentes:
        txt = f"{dados_recentes['AccelY']:.2f}"
        app_instance.lbl_val_accel_y.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_accel_y'): 
            app_instance.lbl_dash_accel_y.configure(text=txt)
    
    # Rodas
    if 'WheelSpeed_FL' in dados_recentes:
        txt = f"{dados_recentes['WheelSpeed_FL']:.0f}"
        app_instance.lbl_val_ws_fl.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_ws_fl'): 
            app_instance.lbl_dash_ws_fl.configure(text=txt)

    if 'WheelSpeed_FR' in dados_recentes:
        txt = f"{dados_recentes['WheelSpeed_FR']:.0f}"
        app_instance.lbl_val_ws_fr.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_ws_fr'): 
            app_instance.lbl_dash_ws_fr.configure(text=txt)

    if 'WheelSpeed_RL' in dados_recentes:
        txt = f"{dados_recentes['WheelSpeed_RL']:.0f}"
        app_instance.lbl_val_ws_rl.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_ws_rl'): 
            app_instance.lbl_dash_ws_rl.configure(text=txt)

    if 'WheelSpeed_RR' in dados_recentes:
        txt = f"{dados_recentes['WheelSpeed_RR']:.0f}"
        app_instance.lbl_val_ws_rr.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_ws_rr'): 
            app_instance.lbl_dash_ws_rr.configure(text=txt)

    # Suspensão
    if 'SuspensionPos_FL' in dados_recentes:
        txt = f"{dados_recentes['SuspensionPos_FL']:.0f}"
        app_instance.lbl_val_susp_fl.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_susp_fl'): 
            app_instance.lbl_dash_susp_fl.configure(text=txt)

    if 'SuspensionPos_FR' in dados_recentes:
        txt = f"{dados_recentes['SuspensionPos_FR']:.0f}"
        app_instance.lbl_val_susp_fr.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_susp_fr'): 
            app_instance.lbl_dash_susp_fr.configure(text=txt)

    if 'SuspensionPos_RL' in dados_recentes:
        txt = f"{dados_recentes['SuspensionPos_RL']:.0f}"
        app_instance.lbl_val_susp_rl.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_susp_rl'): 
            app_instance.lbl_dash_susp_rl.configure(text=txt)

    if 'SuspensionPos_RR' in dados_recentes:
        txt = f"{dados_recentes['SuspensionPos_RR']:.0f}"
        app_instance.lbl_val_susp_rr.configure(text=txt)
        if hasattr(app_instance, 'lbl_dash_susp_rr'): 
            app_instance.lbl_dash_susp_rr.configure(text=txt)
