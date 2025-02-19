class J1939Parser:
    def __init__(self):
        self.pgn_config = {
            61444: {  # Electronic Engine Controller 1 (EEC1)
                'spns': {
                    190: {'start_bit': 24, 'length': 16, 'resolution': 0.125, 'name': 'Engine_Speed'},
                    512: {'start_bit': 8, 'length': 8, 'resolution': 1, 'name': 'Engine_Percent_Load'},
                    513: {'start_bit': 16, 'length': 8, 'resolution': 1, 'name': 'Actual_Engine_Percent_Torque'}
                }
            },
            65262: {  # Engine Temperature 1
                'spns': {
                    110: {'start_bit': 0, 'length': 8, 'resolution': 1, 'name': 'Engine_Coolant_Temperature'},
                    174: {'start_bit': 8, 'length': 8, 'resolution': 1, 'name': 'Fuel_Temperature'}
                }
            },
            65263: {  # Engine Fluid Level/Pressure 1
                'spns': {
                    94: {'start_bit': 0, 'length': 8, 'resolution': 4, 'name': 'Fuel_Delivery_Pressure'},
                    100: {'start_bit': 16, 'length': 8, 'resolution': 4, 'name': 'Engine_Oil_Pressure'}
                }
            },
            65267: {  # Vehicle Position
                'spns': {
                    584: {'start_bit': 0, 'length': 32, 'resolution': 0.0000001, 'name': 'Latitude'},
                    585: {'start_bit': 32, 'length': 32, 'resolution': 0.0000001, 'name': 'Longitude'}
                }
            },
            65269: {  # Ambient Conditions
                'spns': {
                    171: {'start_bit': 0, 'length': 8, 'resolution': 0.5, 'name': 'Ambient_Air_Temperature'},
                    172: {'start_bit': 8, 'length': 8, 'resolution': 0.5, 'name': 'Air_Inlet_Temperature'}
                }
            }
        }
    
    def parse_message(self, msg_id, data):
        pgn = (msg_id >> 8) & 0x1FFFF
        if pgn not in self.pgn_config:
            return None
            
        result = {'pgn': pgn, 'spn_vals': {}}
        
        for spn, config in self.pgn_config[pgn]['spns'].items():
            try:
                start_byte = config['start_bit'] // 8
                bit_offset = config['start_bit'] % 8
                byte_length = (config['length'] + 7) // 8
                
                value = 0
                for i in range(byte_length):
                    if start_byte + i < len(data):
                        value |= data[start_byte + i] << (i * 8)
                
                # Aplica máscara de bits
                value = (value >> bit_offset) & ((1 << config['length']) - 1)
                
                # Aplica resolução
                if 'resolution' in config:
                    value = value * config['resolution']
                    
                result['spn_vals'][config['name']] = value
                
            except Exception as e:
                print(f"Erro ao processar SPN {spn}: {e}")
                
        return result 