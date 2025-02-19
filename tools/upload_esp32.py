import os
import sys
import time
import serial.tools.list_ports

def find_esp32_port():
    """Encontra a porta do ESP32"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "CP210" in port.description or "CH340" in port.description:
            return port.device
    return None

def upload_files():
    """Upload dos arquivos para ESP32"""
    port = find_esp32_port()
    if not port:
        print("ESP32 não encontrado!")
        return False
    
    print(f"ESP32 encontrado na porta {port}")
    
    # Comandos para upload
    commands = [
        f"mpremote connect {port} reset",
        f"mpremote connect {port} fs cp src/esp32/main.py :main.py",
        f"mpremote connect {port} reset"
    ]
    
    for cmd in commands:
        print(f"Executando: {cmd}")
        result = os.system(cmd)
        if result != 0:
            print(f"Erro ao executar: {cmd}")
            return False
        time.sleep(1)
    
    print("Upload concluído com sucesso!")
    return True

if __name__ == "__main__":
    upload_files() 