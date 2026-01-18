"""
Configurador de Fonte de Telemetria - PUCPR Racing

Permite alternar entre diferentes fontes de dados em tempo real:
- CAN Bus (UDP Multicast / SocketCAN)
- LoRa (Serial USB)
- Simulador (para testes)
"""

import json
import os

CONFIG_FILE = "telemetry_source.json"

# Configurações disponíveis
SOURCES = {
    'can_udp': {
        'name': 'CAN Bus (UDP Multicast)',
        'description': 'Recebe mensagens CAN via rede UDP (Windows)',
        'module': 'telemetry_realtime',
        'config': {
            'interface': 'udp_multicast',
            'channel': '239.0.0.1'
        }
    },
    'can_socketcan': {
        'name': 'CAN Bus (SocketCAN)',
        'description': 'Recebe mensagens CAN diretamente (Linux/Raspberry Pi)',
        'module': 'telemetry_realtime',
        'config': {
            'interface': 'socketcan',
            'channel': 'can0'
        }
    },
    'lora_serial': {
        'name': 'LoRa (Serial USB)',
        'description': 'Recebe pacotes LoRa via porta serial',
        'module': 'lora_receiver',
        'config': {
            'port': None,  # Auto-detecta
            'baud_rate': 115200
        }
    },
    'simulator': {
        'name': 'Simulador CAN',
        'description': 'Dados simulados para testes (rodar simulador_carro.py)',
        'module': 'telemetry_realtime',
        'config': {
            'interface': 'udp_multicast',
            'channel': '239.0.0.1'
        }
    }
}


def load_config():
    """Carrega configuração atual."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Padrão: Simulador (mais fácil para testes)
    return {
        'source': 'simulator',
        'last_updated': None
    }


def save_config(source: str):
    """Salva configuração escolhida."""
    from datetime import datetime
    
    config = {
        'source': source,
        'last_updated': datetime.now().isoformat()
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, indent=2, fp=f)
    
    print(f"✓ Configuração salva: {SOURCES[source]['name']}")


def interactive_config():
    """Interface interativa para escolher fonte."""
    print("\n" + "="*60)
    print("   CONFIGURADOR DE FONTE DE TELEMETRIA - PUCPR Racing")
    print("="*60 + "\n")
    
    print("Fontes disponíveis:\n")
    
    for idx, (key, info) in enumerate(SOURCES.items(), 1):
        print(f"  [{idx}] {info['name']}")
        print(f"      {info['description']}")
        print()
    
    # Mostra configuração atual
    current = load_config()
    current_name = SOURCES.get(current['source'], {}).get('name', 'Desconhecido')
    print(f"Fonte atual: {current_name}\n")
    
    # Solicita escolha
    while True:
        try:
            choice = input("Escolha uma fonte (1-4) ou 'q' para sair: ").strip()
            
            if choice.lower() == 'q':
                print("Saindo sem alterar configuração.")
                return
            
            choice_idx = int(choice)
            if 1 <= choice_idx <= len(SOURCES):
                source_key = list(SOURCES.keys())[choice_idx - 1]
                
                # Confirmação
                print(f"\n✓ Selecionado: {SOURCES[source_key]['name']}")
                confirm = input("Confirmar? (s/n): ").strip().lower()
                
                if confirm == 's':
                    save_config(source_key)
                    
                    # Instruções específicas
                    print("\n" + "-"*60)
                    print("PRÓXIMOS PASSOS:")
                    print("-"*60)
                    
                    if source_key == 'lora_serial':
                        print("1. Conecte o receptor LoRa na porta USB")
                        print("2. Verifique a porta no Gerenciador de Dispositivos (Windows)")
                        print("   ou rode: ls /dev/ttyUSB* (Linux)")
                        print("3. Inicie a aplicação: python main.py")
                        print("4. Clique em 'Iniciar Telemetria' na aba Tempo Real")
                    
                    elif source_key == 'simulator':
                        print("1. Em um terminal, rode: python simulador_carro.py")
                        print("2. Em outro terminal, rode: python main.py")
                        print("3. Clique em 'Iniciar Telemetria' na aba Tempo Real")
                    
                    elif 'can' in source_key:
                        print("1. Conecte o dispositivo CAN")
                        print("2. Verifique a interface de rede CAN")
                        print("3. Inicie a aplicação: python main.py")
                        print("4. Clique em 'Iniciar Telemetria' na aba Tempo Real")
                    
                    print("-"*60)
                    break
                else:
                    print("Operação cancelada.")
            else:
                print("Opção inválida. Tente novamente.")
        
        except ValueError:
            print("Entrada inválida. Digite um número de 1 a 4.")
        except KeyboardInterrupt:
            print("\n\nOperação cancelada.")
            break


if __name__ == "__main__":
    interactive_config()
