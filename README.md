# JD Monitor - Dashboard CAN Bus

Monitor de dados CAN Bus para equipamentos John Deere com interface web.

## Características

- Interface web responsiva com Streamlit
- Monitoramento em tempo real
- Gráficos e gauges interativos
- Conexão WiFi configurável
- Leitura de dados via CAN Bus
- Histórico de dados

## Estrutura do Projeto

```
JD_Monitor/
├── src/
│   ├── esp32/
│   │   └── main.py         # Código do ESP32
│   └── dashboard/
│       └── dashboard.py    # Interface web Streamlit
├── requirements.txt
├── README.md
└── LICENSE
```

## Requisitos

### Hardware
- ESP32
- Transceiver CAN
- Conexão WiFi

### Software
- Python 3.7+
- MicroPython (ESP32)
- Bibliotecas Python (ver requirements.txt)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/givanildobrunetta/jd_monitor.git
cd jd_monitor
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Upload do código para ESP32:
```bash
mpremote cp src/esp32/main.py :main.py
mpremote reset
```

4. Execute o dashboard:
```bash
streamlit run src/dashboard/dashboard.py
```

## Uso

1. Conecte ao AP "JD_Monitor" (senha: 12345678)
2. Configure a rede WiFi
3. Acesse o dashboard via navegador
4. Monitore os dados em tempo real

## Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para submeter um Pull Request.

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

## Autor

Givanildo Brunetta - givanildobrunetta@gmail.com
