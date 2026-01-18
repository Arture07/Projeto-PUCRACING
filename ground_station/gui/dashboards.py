"""
Módulo de criação de dashboards de tempo real para telemetria.
Contém funções para criar as interfaces visuais dos dashboards (Motor/ECU, Pilotagem, Rodas, Suspensão).
"""

import customtkinter as ctk
from core.constants import (
    COLOR_BG_PRIMARY, COLOR_BG_SECONDARY, COLOR_BG_TERTIARY,
    COLOR_ACCENT_RED, COLOR_ACCENT_GOLD, COLOR_ACCENT_CYAN, COLOR_ACCENT_GREEN,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER
)


def criar_conteudo_dashboards_tempo_real(app_instance):
    """Cria uma aba extra com sub-abas de dashboards (Tempo Real)."""
    tab_dash = app_instance.tabs_view.tab("📟 Dashboards")
    tab_dash.grid_columnconfigure(0, weight=1)
    tab_dash.grid_rowconfigure(0, weight=1)

    dash_tabs = ctk.CTkTabview(
        tab_dash,
        corner_radius=10,
        fg_color=COLOR_BG_SECONDARY,
        border_width=1,
        border_color=COLOR_BORDER,
        segmented_button_selected_color=COLOR_ACCENT_RED,
        segmented_button_selected_hover_color="#A00000",
        segmented_button_unselected_color=COLOR_BG_SECONDARY,
        segmented_button_fg_color=COLOR_BG_SECONDARY,
        text_color=COLOR_TEXT_PRIMARY,
    )
    dash_tabs.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")

    dash_tabs.add("⚙️ Motor/ECU")
    dash_tabs.add("🧭 Pilotagem")
    dash_tabs.add("🛞 Rodas")
    dash_tabs.add("🛠️ Suspensão")

    criar_dash_motor_ecu(app_instance, dash_tabs.tab("⚙️ Motor/ECU"))
    criar_dash_pilotagem(app_instance, dash_tabs.tab("🧭 Pilotagem"))
    criar_dash_rodas(app_instance, dash_tabs.tab("🛞 Rodas"))
    criar_dash_suspensao(app_instance, dash_tabs.tab("🛠️ Suspensão"))


def criar_dash_motor_ecu(app_instance, parent):
    """Dashboard Motor/ECU com barras de progresso e valores grandes."""
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    main = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    main.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    
    # RPM (destaque principal)
    frpm = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                        border_width=2, border_color=COLOR_ACCENT_RED, height=180)
    frpm.pack(fill="x", pady=(0, 15))
    ctk.CTkLabel(frpm, text="RPM", font=ctk.CTkFont(size=14, weight="bold"), 
                 text_color=COLOR_ACCENT_GOLD).pack(pady=(10, 0))
    app_instance.lbl_dash_rpm = ctk.CTkLabel(frpm, text="0", 
                                             font=ctk.CTkFont(size=56, weight="bold"), 
                                             text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_rpm.pack(pady=(5, 5))
    app_instance.prog_dash_rpm = ctk.CTkProgressBar(frpm, width=400, height=20, 
                                                     corner_radius=10, 
                                                     fg_color=COLOR_BG_SECONDARY, 
                                                     progress_color=COLOR_ACCENT_RED)
    app_instance.prog_dash_rpm.set(0)
    app_instance.prog_dash_rpm.pack(pady=(0, 15))
    
    # Linha: Temp + Lambda
    f1 = ctk.CTkFrame(main, fg_color="transparent")
    f1.pack(fill="x", pady=(0, 15))
    f1.grid_columnconfigure((0, 1), weight=1)
    
    # Temperatura
    ftemp = ctk.CTkFrame(f1, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                         border_width=1, border_color=COLOR_BORDER)
    ftemp.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    ctk.CTkLabel(ftemp, text="TEMPERATURA", font=ctk.CTkFont(size=12, weight="bold"), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(12, 0))
    app_instance.lbl_dash_temp = ctk.CTkLabel(ftemp, text="0", 
                                              font=ctk.CTkFont(size=40, weight="bold"), 
                                              text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_temp.pack(pady=(5, 0))
    ctk.CTkLabel(ftemp, text="°C", font=ctk.CTkFont(size=14), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 12))
    
    # Lambda
    flam = ctk.CTkFrame(f1, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                        border_width=1, border_color=COLOR_BORDER)
    flam.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    ctk.CTkLabel(flam, text="LAMBDA", font=ctk.CTkFont(size=12, weight="bold"), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(12, 0))
    app_instance.lbl_dash_lambda = ctk.CTkLabel(flam, text="0.00", 
                                                font=ctk.CTkFont(size=40, weight="bold"), 
                                                text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_lambda.pack(pady=(5, 0))
    ctk.CTkLabel(flam, text="λ", font=ctk.CTkFont(size=14), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 12))
    
    # TPS com barra
    ftps = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                        border_width=1, border_color=COLOR_BORDER)
    ftps.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(ftps, text="THROTTLE POSITION (TPS)", 
                 font=ctk.CTkFont(size=12, weight="bold"), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(12, 5))
    app_instance.lbl_dash_tps = ctk.CTkLabel(ftps, text="0%", 
                                             font=ctk.CTkFont(size=32, weight="bold"), 
                                             text_color=COLOR_ACCENT_GOLD)
    app_instance.lbl_dash_tps.pack(pady=(0, 5))
    app_instance.prog_dash_tps = ctk.CTkProgressBar(ftps, width=350, height=16, 
                                                     corner_radius=8, 
                                                     fg_color=COLOR_BG_SECONDARY, 
                                                     progress_color=COLOR_ACCENT_GOLD)
    app_instance.prog_dash_tps.set(0)
    app_instance.prog_dash_tps.pack(pady=(0, 12))


def criar_dash_pilotagem(app_instance, parent):
    """Dashboard Pilotagem com Brake em destaque e IMU separado."""
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    main = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    main.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    
    # Linha: Volante + Brake
    f1 = ctk.CTkFrame(main, fg_color="transparent")
    f1.pack(fill="x", pady=(0, 15))
    f1.grid_columnconfigure((0, 1), weight=1)
    
    # Volante
    fvol = ctk.CTkFrame(f1, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                        border_width=1, border_color=COLOR_BORDER)
    fvol.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    ctk.CTkLabel(fvol, text="VOLANTE", font=ctk.CTkFont(size=12, weight="bold"), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(12, 0))
    app_instance.lbl_dash_steer = ctk.CTkLabel(fvol, text="0", 
                                               font=ctk.CTkFont(size=40, weight="bold"), 
                                               text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_steer.pack(pady=(5, 0))
    ctk.CTkLabel(fvol, text="graus", font=ctk.CTkFont(size=14), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 12))
    
    # Brake com barra
    fbrk = ctk.CTkFrame(f1, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                        border_width=2, border_color=COLOR_ACCENT_RED)
    fbrk.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    ctk.CTkLabel(fbrk, text="PRESSÃO DE FREIO", 
                 font=ctk.CTkFont(size=12, weight="bold"), 
                 text_color=COLOR_ACCENT_RED).pack(pady=(12, 5))
    app_instance.lbl_dash_brake = ctk.CTkLabel(fbrk, text="0", 
                                               font=ctk.CTkFont(size=40, weight="bold"), 
                                               text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_brake.pack(pady=(0, 5))
    ctk.CTkLabel(fbrk, text="bar", font=ctk.CTkFont(size=12), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 5))
    app_instance.prog_dash_brake = ctk.CTkProgressBar(fbrk, width=280, height=16, 
                                                       corner_radius=8, 
                                                       fg_color=COLOR_BG_SECONDARY, 
                                                       progress_color=COLOR_ACCENT_RED)
    app_instance.prog_dash_brake.set(0)
    app_instance.prog_dash_brake.pack(pady=(0, 12))
    
    # IMU Section
    fimu = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                        border_width=1, border_color=COLOR_ACCENT_CYAN)
    fimu.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(fimu, text="⚡ ACELERAÇÃO (G-FORCE)", 
                 font=ctk.CTkFont(size=13, weight="bold"), 
                 text_color=COLOR_ACCENT_CYAN).pack(pady=(12, 10))
    
    f_imu_grid = ctk.CTkFrame(fimu, fg_color="transparent")
    f_imu_grid.pack(fill="x", padx=15, pady=(0, 12))
    f_imu_grid.grid_columnconfigure((0, 1), weight=1)
    
    # Accel X (Longitudinal)
    fax = ctk.CTkFrame(f_imu_grid, fg_color=COLOR_BG_SECONDARY, corner_radius=10)
    fax.grid(row=0, column=0, sticky="nsew", padx=(0, 7), pady=5)
    ctk.CTkLabel(fax, text="LONGITUDINAL", font=ctk.CTkFont(size=11), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(10, 0))
    app_instance.lbl_dash_accel_x = ctk.CTkLabel(fax, text="0.0", 
                                                  font=ctk.CTkFont(size=36, weight="bold"), 
                                                  text_color=COLOR_ACCENT_GOLD)
    app_instance.lbl_dash_accel_x.pack(pady=(3, 0))
    ctk.CTkLabel(fax, text="g", font=ctk.CTkFont(size=12), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 10))
    
    # Accel Y (Lateral)
    fay = ctk.CTkFrame(f_imu_grid, fg_color=COLOR_BG_SECONDARY, corner_radius=10)
    fay.grid(row=0, column=1, sticky="nsew", padx=(7, 0), pady=5)
    ctk.CTkLabel(fay, text="LATERAL", font=ctk.CTkFont(size=11), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(10, 0))
    app_instance.lbl_dash_accel_y = ctk.CTkLabel(fay, text="0.0", 
                                                  font=ctk.CTkFont(size=36, weight="bold"), 
                                                  text_color=COLOR_ACCENT_GOLD)
    app_instance.lbl_dash_accel_y.pack(pady=(3, 0))
    ctk.CTkLabel(fay, text="g", font=ctk.CTkFont(size=12), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 10))


def criar_dash_rodas(app_instance, parent):
    """Dashboard Rodas 2x2 com cores diferenciadas (Gold frontal, Red traseira)."""
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    main = ctk.CTkFrame(parent, fg_color="transparent")
    main.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    main.grid_columnconfigure((0, 1), weight=1, uniform="rodas")
    main.grid_rowconfigure((0, 1), weight=1, uniform="rodas")
    
    # FL (frontal esquerda - Gold)
    ffl = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_GOLD)
    ffl.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
    ctk.CTkLabel(ffl, text="🔸 RODA FRONTAL ESQUERDA", 
                 font=ctk.CTkFont(size=11, weight="bold"), 
                 text_color=COLOR_ACCENT_GOLD).pack(pady=(15, 5))
    app_instance.lbl_dash_ws_fl = ctk.CTkLabel(ffl, text="0", 
                                               font=ctk.CTkFont(size=52, weight="bold"), 
                                               text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_ws_fl.pack(pady=(5, 0))
    ctk.CTkLabel(ffl, text="km/h", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))
    
    # FR (frontal direita - Gold)
    ffr = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_GOLD)
    ffr.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
    ctk.CTkLabel(ffr, text="🔸 RODA FRONTAL DIREITA", 
                 font=ctk.CTkFont(size=11, weight="bold"), 
                 text_color=COLOR_ACCENT_GOLD).pack(pady=(15, 5))
    app_instance.lbl_dash_ws_fr = ctk.CTkLabel(ffr, text="0", 
                                               font=ctk.CTkFont(size=52, weight="bold"), 
                                               text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_ws_fr.pack(pady=(5, 0))
    ctk.CTkLabel(ffr, text="km/h", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))
    
    # RL (traseira esquerda - Red)
    frl = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_RED)
    frl.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))
    ctk.CTkLabel(frl, text="🔴 RODA TRASEIRA ESQUERDA", 
                 font=ctk.CTkFont(size=11, weight="bold"), 
                 text_color=COLOR_ACCENT_RED).pack(pady=(15, 5))
    app_instance.lbl_dash_ws_rl = ctk.CTkLabel(frl, text="0", 
                                               font=ctk.CTkFont(size=52, weight="bold"), 
                                               text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_ws_rl.pack(pady=(5, 0))
    ctk.CTkLabel(frl, text="km/h", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))
    
    # RR (traseira direita - Red)
    frr = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_RED)
    frr.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))
    ctk.CTkLabel(frr, text="🔴 RODA TRASEIRA DIREITA", 
                 font=ctk.CTkFont(size=11, weight="bold"), 
                 text_color=COLOR_ACCENT_RED).pack(pady=(15, 5))
    app_instance.lbl_dash_ws_rr = ctk.CTkLabel(frr, text="0", 
                                               font=ctk.CTkFont(size=52, weight="bold"), 
                                               text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_ws_rr.pack(pady=(5, 0))
    ctk.CTkLabel(frr, text="km/h", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))


def criar_dash_suspensao(app_instance, parent):
    """Dashboard Suspensão 2x2 com cores diferenciadas (Cyan frontal, Green traseira)."""
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    
    main = ctk.CTkFrame(parent, fg_color="transparent")
    main.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    main.grid_columnconfigure((0, 1), weight=1, uniform="susp")
    main.grid_rowconfigure((0, 1), weight=1, uniform="susp")
    
    # FL (frontal esquerda - Cyan)
    ffl = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_CYAN)
    ffl.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
    ctk.CTkLabel(ffl, text="💠 SUSPENSÃO FRONTAL ESQUERDA", 
                 font=ctk.CTkFont(size=10, weight="bold"), 
                 text_color=COLOR_ACCENT_CYAN).pack(pady=(15, 5))
    app_instance.lbl_dash_susp_fl = ctk.CTkLabel(ffl, text="0", 
                                                  font=ctk.CTkFont(size=48, weight="bold"), 
                                                  text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_susp_fl.pack(pady=(5, 0))
    ctk.CTkLabel(ffl, text="mm", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))
    
    # FR (frontal direita - Cyan)
    ffr = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_CYAN)
    ffr.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
    ctk.CTkLabel(ffr, text="💠 SUSPENSÃO FRONTAL DIREITA", 
                 font=ctk.CTkFont(size=10, weight="bold"), 
                 text_color=COLOR_ACCENT_CYAN).pack(pady=(15, 5))
    app_instance.lbl_dash_susp_fr = ctk.CTkLabel(ffr, text="0", 
                                                  font=ctk.CTkFont(size=48, weight="bold"), 
                                                  text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_susp_fr.pack(pady=(5, 0))
    ctk.CTkLabel(ffr, text="mm", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))
    
    # RL (traseira esquerda - Green)
    frl = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_GREEN)
    frl.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))
    ctk.CTkLabel(frl, text="🟢 SUSPENSÃO TRASEIRA ESQUERDA", 
                 font=ctk.CTkFont(size=10, weight="bold"), 
                 text_color=COLOR_ACCENT_GREEN).pack(pady=(15, 5))
    app_instance.lbl_dash_susp_rl = ctk.CTkLabel(frl, text="0", 
                                                  font=ctk.CTkFont(size=48, weight="bold"), 
                                                  text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_susp_rl.pack(pady=(5, 0))
    ctk.CTkLabel(frl, text="mm", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))
    
    # RR (traseira direita - Green)
    frr = ctk.CTkFrame(main, fg_color=COLOR_BG_TERTIARY, corner_radius=12, 
                       border_width=3, border_color=COLOR_ACCENT_GREEN)
    frr.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))
    ctk.CTkLabel(frr, text="🟢 SUSPENSÃO TRASEIRA DIREITA", 
                 font=ctk.CTkFont(size=10, weight="bold"), 
                 text_color=COLOR_ACCENT_GREEN).pack(pady=(15, 5))
    app_instance.lbl_dash_susp_rr = ctk.CTkLabel(frr, text="0", 
                                                  font=ctk.CTkFont(size=48, weight="bold"), 
                                                  text_color=COLOR_TEXT_PRIMARY)
    app_instance.lbl_dash_susp_rr.pack(pady=(5, 0))
    ctk.CTkLabel(frr, text="mm", font=ctk.CTkFont(size=16), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 15))


def criar_card_sensor(app_instance, parent, row, col, titulo, valor_inicial, unidade):
    """Cria card simples de sensor (método legado para compatibilidade)."""
    frame = ctk.CTkFrame(parent, fg_color=COLOR_BG_TERTIARY, corner_radius=10, 
                         border_width=1, border_color=COLOR_BORDER)
    frame.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
    
    ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(size=12, weight="bold"), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(10, 2))
    
    lbl_valor = ctk.CTkLabel(frame, text=valor_inicial, 
                             font=ctk.CTkFont(size=20, weight="bold"), 
                             text_color=COLOR_TEXT_PRIMARY)
    lbl_valor.pack(pady=(0, 2))
    
    ctk.CTkLabel(frame, text=unidade, font=ctk.CTkFont(size=10), 
                 text_color=COLOR_TEXT_SECONDARY).pack(pady=(0, 10))
    
    return lbl_valor
