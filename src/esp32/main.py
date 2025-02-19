# type: ignore
import network
import socket
import time
from machine import Pin, SPI
import json
import struct

# Configurações
AP_SSID = "JD_Monitor"
AP_PASSWORD = "12345678"
LED = Pin(2, Pin.OUT)

# Configuração CAN/ISOBUS
CAN_TX = 5
CAN_RX = 4 
CAN_CS = 15
CAN_SCK = 14
CAN_SPEED = 250000

# HTML do Portal de Configuração WiFi
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
            <input type="password" name="password" placeholder="Senha">
            <br><br>
            <input type="submit" value="Conectar">
        </form>
    </div>
    <pre>{log}</pre>
</body>
</html>
"""

# HTML do Monitor
MONITOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JD Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
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
        <h3>Dados:</h3>
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
wifi_config = {}

# Definições ISOBUS/J1939
class ISOBUS:
    # PGNs John Deere
    PGN = {
        0xF004: {  # Electronic Engine Controller 1
            'spns': {
                190: {'name': 'engine_speed', 'offset': 3, 'length': 2, 'resolution': 0.125, 'unit': 'rpm'},
                91: {'name': 'throttle', 'offset': 1, 'length': 1, 'resolution': 0.4, 'unit': '%'}
            }
        },
        0xFEF1: {  # Vehicle Speed
            'spns': {
                84: {'name': 'wheel_speed', 'offset': 1, 'length': 2, 'resolution': 0.00390625, 'unit': 'km/h'}
            }
        },
        0xFEEE: {  # Engine Temperature
            'spns': {
                110: {'name': 'coolant_temp', 'offset': 0, 'length': 1, 'resolution': 1, 'offset_value': -40, 'unit': '°C'},
                175: {'name': 'oil_temp', 'offset': 1, 'length': 1, 'resolution': 1, 'offset_value': -40, 'unit': '°C'}
            }
        },
        0xFEF2: {  # Fuel Economy
            'spns': {
                183: {'name': 'fuel_rate', 'offset': 2, 'length': 2, 'resolution': 0.05, 'unit': 'L/h'},
                96: {'name': 'fuel_level', 'offset': 1, 'length': 1, 'resolution': 0.4, 'unit': '%'}
            }
        },
        0xF003: {  # Engine Load
            'spns': {
                92: {'name': 'load', 'offset': 2, 'length': 1, 'resolution': 0.4, 'unit': '%'}
            }
        }
    }

    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.data = {
            'status': {
                'connected': True,
                'messages_per_second': 0,
                'errors': 0
            },
            'engine': {},
            'vehicle': {},
            'raw_messages': []
        }
        self.msg_count = 0
        self.last_count = time.time()
        self._init_can()

    def _init_can(self):
        """Inicializa controlador CAN"""
        self.cs.value(0)
        try:
            # Reset
            self.spi.write(bytes([0xC0]))
            time.sleep_ms(10)
            
            # Configura 250kbps
            self.spi.write(bytes([0x02, 0x90]))  # CNF1
            self.spi.write(bytes([0x03, 0xB5]))  # CNF2
            self.spi.write(bytes([0x04, 0x01]))  # CNF3
            
            # Configura filtros para PGNs específicos
            for i, pgn in enumerate(self.PGN.keys()):
                if i < 6:  # Máximo 6 filtros
                    mask = (pgn << 8) & 0xFFFFFF00
                    self.spi.write(bytes([0x20 + i*4] + list((mask).to_bytes(4, 'big'))))
            
            # Modo normal
            self.spi.write(bytes([0x0F, 0x00]))
            
        finally:
            self.cs.value(1)

    def _extract_bits(self, data, offset, length, resolution=1, offset_value=0):
        """Extrai valor dos bytes"""
        if offset + length > len(data):
            return 0
            
        value = 0
        for i in range(length):
            value = (value << 8) | data[offset + i]
            
        return value * resolution + offset_value

    def _process_pgn(self, pgn, data):
        """Processa PGN específico"""
        if pgn not in self.PGN:
            return
            
        pgn_data = self.PGN[pgn]
        for spn, spn_def in pgn_data['spns'].items():
            try:
                value = self._extract_bits(
                    data,
                    spn_def['offset'],
                    spn_def['length'],
                    spn_def.get('resolution', 1),
                    spn_def.get('offset_value', 0)
                )
                
                # Organiza por categoria
                if 'engine' in spn_def['name']:
                    self.data['engine'][spn_def['name']] = value
                else:
                    self.data['vehicle'][spn_def['name']] = value
                    
            except Exception as e:
                print(f"Erro processando SPN {spn}: {str(e)}")
                self.data['status']['errors'] += 1

    def read_message(self):
        """Lê e processa mensagem CAN"""
        self.cs.value(0)
        try:
            self.spi.write(bytes([0x90]))
            status = self.spi.read(1)[0]
            
            if status & 0x03:
                self.spi.write(bytes([0x92]))
                data = self.spi.read(13)
                
                can_id = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
                dlc = data[4] & 0x0F
                msg_data = data[5:5+dlc]
                
                # Extrai PGN
                pgn = (can_id >> 8) & 0x1FFFF
                
                # Processa dados
                self._process_pgn(pgn, msg_data)
                
                # Atualiza contagem
                self.msg_count += 1
                if time.time() - self.last_count >= 1:
                    self.data['status']['messages_per_second'] = self.msg_count
                    self.msg_count = 0
                    self.last_count = time.time()
                
                # Guarda mensagem raw
                self.data['raw_messages'].insert(0, f"ID: {hex(can_id)} Data: {bytes(msg_data).hex()}")
                if len(self.data['raw_messages']) > 20:
                    self.data['raw_messages'].pop()
                    
                return True
                
        finally:
            self.cs.value(1)
        return False

    def get_data(self):
        """Retorna dados processados"""
        return self.data

def log(msg):
    """Adiciona mensagem ao log"""
    print(msg)
    log_messages.insert(0, f"{time.time()}: {msg}")
    if len(log_messages) > 10:
        log_messages.pop()

def start_ap():
    """Inicia Access Point"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, 
              password=AP_PASSWORD,
              authmode=network.AUTH_WPA2_PSK)
    
    while not ap.active():
        LED.value(not LED.value())
        time.sleep(0.5)
    
    log(f"AP iniciado: {AP_SSID}")
    return ap

def connect_wifi(ssid, password):
    """Conecta a rede WiFi"""
    global wifi_config
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    try:
        log(f"Conectando a {ssid}...")
        wlan.connect(ssid, password)
        
        # Aguarda conexão
        max_wait = 20
        while max_wait > 0:
            if wlan.isconnected():
                wifi_config = {
                    'ssid': ssid,
                    'password': password,
                    'ip': wlan.ifconfig()[0]
                }
                log(f"Conectado! IP: {wifi_config['ip']}")
                return True
            max_wait -= 1
            time.sleep(1)
            LED.value(not LED.value())
            
        log("Timeout na conexão")
        return False
        
    except Exception as e:
        log(f"Erro ao conectar: {str(e)}")
        return False

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

def handle_api_request(conn, isobus):
    """Processa requisição API"""
    data = isobus.get_data() if isobus else {}
    response = json.dumps(data)
    
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: application/json\n')
    conn.send('Access-Control-Allow-Origin: *\n')
    conn.send('Connection: close\n\n')
    conn.send(response.encode())

def handle_web_request(conn, isobus):
    """Processa requisição web"""
    try:
        data = isobus.get_data() if isobus else {
            'status': {'connected': False, 'messages_per_second': 0, 'errors': 0},
            'engine': {},
            'vehicle': {},
            'raw_messages': []
        }
        
        html = MONITOR_HTML.format(
            wifi_ssid=wifi_config.get('ssid', ''),
            wifi_ip=wifi_config.get('ip', ''),
            wifi_signal=wlan.status('rssi') if wlan.isconnected() else 0,
            can_data='\n'.join(data['raw_messages'][-10:])
        )
        
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.send(html.encode())
        
    except Exception as e:
        print(f"Erro ao gerar página: {str(e)}")
        conn.send('HTTP/1.1 500 Internal Server Error\n\n')
        conn.send('Erro ao gerar página'.encode())

def web_server():
    """Servidor web"""
    s = socket.socket()
    s.bind(('', 80))
    s.listen(5)
    
    # Inicia CAN
    isobus = ISOBUS(SPI(1,
              baudrate=10000000,
              polarity=0,
              phase=0,
              sck=Pin(CAN_SCK),
              mosi=Pin(CAN_TX),
              miso=Pin(CAN_RX)),
              Pin(CAN_CS, Pin.OUT))
    
    # Inicia em modo AP
    ap = start_ap()
    wlan = None
    
    log('Servidor web iniciado')
    status = 'Aguardando conexão'
    
    while True:
        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode()
            LED.value(not LED.value())
            
            # API Endpoint
            if '/api/data' in request:
                handle_api_request(conn, isobus)
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
                if isobus:
                    isobus.read_message()
                
                # Página de monitoramento
                wlan = network.WLAN(network.STA_IF)
                response = MONITOR_HTML.format(
                    wifi_ssid=wifi_config.get('ssid', ''),
                    wifi_ip=wifi_config.get('ip', ''),
                    wifi_signal=wlan.status('rssi') if wlan.isconnected() else 0,
                    can_data='\n'.join(isobus.get_data()['raw_messages'][-10:]) if isobus else ''
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