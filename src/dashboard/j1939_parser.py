from datetime import datetime
import struct

class J1939Parser:
    """Parser para mensagens CAN no protocolo J1939"""
    
    # PGNs (Parameter Group Numbers) comuns
    PGN = {
        0xF004: "Electronic Engine Controller 1",
        0xFEF1: "Cruise Control/Vehicle Speed",
        0xFEEE: "Engine Temperature",
        0xFEF2: "Fuel Economy",
        0xFEF7: "Vehicle Position",
        0xF003: "Engine Load",
        0xFEF6: "Intake/Exhaust Conditions",
        0xF000: "Retarder",
        0xFEF5: "Engine Hours/Revolutions",
        0xFEE9: "Engine Fluid Level/Pressure"
    }

    def __init__(self):
        self.last_values = {}

    def get_pgn(self, can_id):
        """Extrai PGN do ID CAN"""
        return (can_id >> 8) & 0x1FFFF

    def parse_message(self, msg):
        """Processa uma mensagem CAN"""
        try:
            # Extrai ID e dados
            id_hex = msg.split("ID: ")[1].split(" Data:")[0]
            data_hex = msg.split("Data: ")[1].strip()
            
            can_id = int(id_hex, 16)
            can_data = bytes.fromhex(data_hex)
            
            pgn = self.get_pgn(can_id)
            timestamp = datetime.now()
            
            # Processa baseado no PGN
            if pgn == 0xF004:  # Electronic Engine Controller 1
                return self._parse_engine_data(timestamp, can_data)
            elif pgn == 0xFEF1:  # Vehicle Speed
                return self._parse_vehicle_speed(timestamp, can_data)
            elif pgn == 0xFEEE:  # Engine Temperature
                return self._parse_temperature(timestamp, can_data)
            elif pgn == 0xFEF2:  # Fuel Economy
                return self._parse_fuel(timestamp, can_data)
            elif pgn == 0xF003:  # Engine Load
                return self._parse_load(timestamp, can_data)
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {str(e)}")
            return None

    def _parse_engine_data(self, timestamp, data):
        """Processa dados do motor"""
        try:
            rpm = struct.unpack('>H', data[3:5])[0] * 0.125
            throttle = data[1] * 0.4
            
            return [{
                "timestamp": timestamp,
                "tipo": "RPM",
                "valor": rpm,
                "unidade": "RPM"
            }, {
                "timestamp": timestamp,
                "tipo": "Acelerador",
                "valor": throttle,
                "unidade": "%"
            }]
        except:
            return None

    def _parse_vehicle_speed(self, timestamp, data):
        """Processa velocidade do veículo"""
        try:
            speed = struct.unpack('>H', data[1:3])[0] * 0.00390625
            return [{
                "timestamp": timestamp,
                "tipo": "Velocidade",
                "valor": speed,
                "unidade": "km/h"
            }]
        except:
            return None

    def _parse_temperature(self, timestamp, data):
        """Processa temperaturas"""
        try:
            engine_temp = data[0] - 40
            oil_temp = data[1] - 40
            
            return [{
                "timestamp": timestamp,
                "tipo": "Temperatura Motor",
                "valor": engine_temp,
                "unidade": "°C"
            }, {
                "timestamp": timestamp,
                "tipo": "Temperatura Óleo",
                "valor": oil_temp,
                "unidade": "°C"
            }]
        except:
            return None

    def _parse_fuel(self, timestamp, data):
        """Processa dados de combustível"""
        try:
            level = data[1] * 0.4
            rate = struct.unpack('>H', data[2:4])[0] * 0.05
            
            return [{
                "timestamp": timestamp,
                "tipo": "Nível Combustível",
                "valor": level,
                "unidade": "%"
            }, {
                "timestamp": timestamp,
                "tipo": "Consumo",
                "valor": rate,
                "unidade": "L/h"
            }]
        except:
            return None

    def _parse_load(self, timestamp, data):
        """Processa carga do motor"""
        try:
            load = data[2] * 0.4
            return [{
                "timestamp": timestamp,
                "tipo": "Carga Motor",
                "valor": load,
                "unidade": "%"
            }]
        except:
            return None 