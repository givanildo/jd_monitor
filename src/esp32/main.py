# type: ignore
import network
import socket
import time
from machine import Pin, SPI
import json

# Configuração dos pinos CAN
CAN_TX = 5  # GPIO5 (MOSI)
CAN_RX = 4  # GPIO4 (MISO)
CAN_CS = 15 # GPIO15 (CS)
CAN_SCK = 14 # GPIO14 (SCK)
CAN_SPEED = 250000  # 250kbps

# LED para status
led = Pin(2, Pin.OUT)

# Configurações
AP_SSID = "JD_Monitor"
AP_PASSWORD = "12345678"

# HTML para configuração WiFi
CONFIG_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JD Monitor - Config</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <h2>John Deere Monitor - Configuração</h2>
    <div>Status: {status}</div>
    
    <div>
        <h3>Redes WiFi:</h3>
        <form method="post" action="/connect">
            <select name="ssid">{networks}</select>
            <br><br>
            <input type="text" name="password" value="">
            <br><br>
            <input type="submit" value="Conectar">
        </form>
    </div>
    <pre>{log}</pre>
</body>
</html>
"""

# HTML para monitoramento CAN
MONITOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JD Monitor - CAN</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="1">
</head>
<body>
    <h2>Monitor CAN Bus</h2>
    <div>
        <h3>Status:</h3>
        <p>Rede: {wifi_ssid}</p>
        <p>IP: {wifi_ip}</p>
        <p>Sinal: {wifi_signal}dBm</p>
    </div>
    <div>
        <h3>Terminal CAN:</h3>
        <pre style="background:#000;color:#0f0;padding:10px">{can_data}</pre>
    </div>
    <form method="post" action="/reset">
        <input type="submit" value="Resetar WiFi">
    </form>
</body>
</html>
"""

# Variáveis globais
log_messages = []
can_messages = []
wifi_config = {}

def log(msg):
    """Adiciona mensagem ao log"""
    print(msg)
    log_messages.insert(0, f"{time.time()}: {msg}")
    if len(log_messages) > 10:
        log_messages.pop()

def init_can():
    """Inicializa interface CAN via SPI"""
    try:
        # Configura pinos
        cs = Pin(CAN_CS, Pin.OUT)
        cs.value(1)  # CS inativo
        
        # Configura SPI
        spi = SPI(1,
                  baudrate=10000000,
                  polarity=0,
                  phase=0,
                  sck=Pin(CAN_SCK),
                  mosi=Pin(CAN_TX),
                  miso=Pin(CAN_RX))
        
        log("Interface CAN inicializada")
        return {"spi": spi, "cs": cs}
    except Exception as e:
        log(f"Erro CAN: {str(e)}")
        return None

def read_can(can_if):
    """Lê mensagens CAN via SPI"""
    try:
        spi = can_if["spi"]
        cs = can_if["cs"]
        
        cs.value(0)  # Ativa CS
        data = spi.read(13)  # Lê 13 bytes
        cs.value(1)  # Desativa CS
        
        if data and len(data) >= 13:
            can_id = (data[0] << 3) | (data[1] >> 5)
            dlc = data[1] & 0x0F
            can_data = data[2:2+dlc]
            
            can_messages.insert(0, f"ID: {hex(can_id)} Data: {bytes(can_data).hex()}")
            if len(can_messages) > 20:
                can_messages.pop()
    except Exception as e:
        log(f"Erro leitura CAN: {str(e)}")

def connect_wifi(ssid, password):
    """Conecta a uma rede WiFi"""
    global wifi_config
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    log(f"Conectando a {ssid}...")
    try:
        wlan.connect(ssid, password)
        
        # Aguarda conexão
        for _ in range(20):
            if wlan.isconnected():
                log("Conectado!")
                wifi_config = {
                    'ssid': ssid,
                    'password': password,
                    'ip': wlan.ifconfig()[0]
                }
                return True
            led.value(not led.value())
            time.sleep(1)
    except:
        pass
        
    log("Falha ao conectar")
    return False

def start_ap():
    """Inicia Access Point"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, 
              password=AP_PASSWORD,
              authmode=network.AUTH_WPA2_PSK)
    
    while not ap.active():
        led.value(not led.value())
        time.sleep(0.5)
    
    log(f"AP iniciado: {AP_SSID}")
    return ap

def scan_networks():
    """Escaneia redes WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        networks = wlan.scan()
        return '\n'.join([
            f'<option value="{net[0].decode()}">{net[0].decode()} ({net[3]}dB)</option>'
            for net in networks
        ])
    except:
        return '<option value="">Erro ao buscar redes</option>'

def handle_api_request(conn, wlan):
    """Processa requisição da API"""
    response = json.dumps({
        'wifi_ssid': wifi_config.get('ssid', ''),
        'wifi_ip': wifi_config.get('ip', ''),
        'wifi_signal': wlan.status('rssi') if wlan and wlan.isconnected() else 0,
        'can_messages': can_messages
    })
    
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: application/json\n')
    conn.send('Access-Control-Allow-Origin: *\n')
    conn.send('Connection: close\n\n')
    conn.send(response.encode())

def web_server():
    """Servidor web"""
    s = socket.socket()
    s.bind(('', 80))
    s.listen(5)
    
    # Inicia CAN
    can_if = init_can()
    
    # Inicia em modo AP
    ap = start_ap()
    wlan = None
    
    log('Servidor web iniciado')
    status = 'Aguardando conexão'
    
    while True:
        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode()
            led.value(not led.value())
            
            # API Endpoint
            if '/api/data' in request:
                handle_api_request(conn, wlan)
                conn.close()
                continue
            
            # Modo AP - Configuração
            if not wifi_config:
                if 'POST /connect' in request:
                    try:
                        form = request.split('\r\n\r\n')[1]
                        ssid = form.split('ssid=')[1].split('&')[0]
                        password = form.split('password=')[1].split('&')[0]
                        if connect_wifi(ssid, password):
                            status = f'Conectado a {ssid}'
                            ap.active(False)  # Desliga AP
                        else:
                            status = 'Falha ao conectar'
                    except Exception as e:
                        log(f"Erro ao conectar: {str(e)}")
                        status = 'Erro ao conectar'
                
                # Página de configuração
                networks = scan_networks()
                response = CONFIG_HTML.format(
                    status=status,
                    networks=networks,
                    log='\n'.join(log_messages)
                )
            
            # Modo conectado - Monitoramento
            else:
                if 'POST /reset' in request:
                    wifi_config.clear()
                    if wlan:
                        wlan.active(False)
                    ap = start_ap()
                    status = 'WiFi resetado'
                    continue
                
                # Lê CAN
                if can_if:
                    read_can(can_if)
                
                # Página de monitoramento
                wlan = network.WLAN(network.STA_IF)
                response = MONITOR_HTML.format(
                    wifi_ssid=wifi_config.get('ssid', ''),
                    wifi_ip=wifi_config.get('ip', ''),
                    wifi_signal=wlan.status('rssi') if wlan.isconnected() else 0,
                    can_data='\n'.join(can_messages)
                )
            
            # Envia resposta
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.send(response.encode())
            conn.close()
            
        except Exception as e:
            log(f'Erro: {str(e)}')
            try:
                conn.close()
            except:
                pass
        time.sleep(0.1)

# Inicia servidor
web_server()