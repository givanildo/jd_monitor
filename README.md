# Monitor CAN Bus - John Deere

Monitor para dados ISOBUS/J1939 de tratores John Deere usando ESP32 e Streamlit.

## Características

- Leitura de dados CAN Bus em tempo real
- Interface web responsiva
- Visualização de métricas do motor e veículo
- Gráficos históricos e análises
- Filtros e configurações personalizáveis
- Suporte ao protocolo ISOBUS/J1939

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/givanildo/can_bus_monitor.git
cd can_bus_monitor
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração do ESP32

1. Conecte o ESP32 via USB

2. Upload do código:
```bash
python tools/upload_esp32.py
```

3. Conecte ao AP do ESP32:
- SSID: JD_Monitor
- Senha: 12345678

4. Configure a rede WiFi através do portal web

## Executando o Dashboard

```bash
streamlit run src/dashboard/dashboard.py
```

## Estrutura do Projeto

- `src/dashboard/`: Código do dashboard Streamlit
- `src/esp32/`: Código do ESP32 e parser ISOBUS
- `tools/`: Utilitários e scripts
- `requirements.txt`: Dependências do projeto

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Autor

Givanildo Brunetta - givanildobrunetta@gmail.com

## Créditos

- Baseado no protocolo ISOBUS/J1939
- Inspirado no [pysobus](https://github.com/FarmLogs/pysobus)
