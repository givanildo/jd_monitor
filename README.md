# 🚜 Monitor CAN Bus para Tratores John Deere

Este projeto implementa um sistema de monitoramento CAN bus para tratores John Deere usando ESP32 e dashboard web em Streamlit. O sistema permite a leitura, decodificação e visualização em tempo real dos dados do trator através do protocolo J1939.

## 📋 Características

- Leitura de CAN bus a 250kbps
- Decodificação de mensagens J1939
- Servidor web embutido no ESP32
- Dashboard em tempo real com Streamlit
- Filtros por categoria de dados
- Histórico de mensagens
- Visualização de dados em gráficos
- Suporte a GPS e dados de posicionamento

### 📊 Dados Monitorados

- **Motor**
  - RPM
  - Carga do motor
  - Torque
  - Temperatura do líquido de arrefecimento
  - Temperatura do combustível
  - Pressão do óleo
  - Pressão do combustível

- **Posição**
  - Latitude
  - Longitude
  - Altitude
  - Velocidade

- **Ambiente**
  - Temperatura ambiente
  - Temperatura do ar de admissão

- **Implemento**
  - Status diversos do implemento

## 🛠️ Hardware Necessário

- ESP32 (recomendado: ESP32-WROOM-32)
- Transceiver CAN (MCP2515 ou TJA1050)
- Conector diagnóstico J1939
- Resistores terminadores 120Ω (2x)

## 📥 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/nome-do-repo.git
cd nome-do-repo
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o WiFi no arquivo `web_server.py`:
```python
wlan.connect('sua_rede', 'sua_senha')
```

4. Carregue os arquivos no ESP32:
```bash
mpremote cp main.py :main.py
mpremote cp web_server.py :web_server.py
mpremote cp j1939_parser.py :j1939_parser.py
```

## 🚀 Uso

1. Conecte o ESP32 ao barramento CAN do trator
2. Inicie o servidor web no ESP32
3. Execute o dashboard Streamlit:
```bash
streamlit run dashboard.py
```

### 🌐 API Web

O servidor web suporta os seguintes endpoints:

- `/dados` - Todos os dados
- `/dados?categoria=motor,posicao` - Dados específicos por categoria
- `/dados?historico=motor` - Histórico de dados
- `/dados?estatisticas=true` - Estatísticas de mensagens

## 📊 Dashboard

O dashboard Streamlit oferece:
- Visualização em tempo real dos dados do motor
- Gráficos históricos
- Mapa de posicionamento
- Indicadores de temperatura e pressão
- Estatísticas de mensagens CAN

## 🔌 Pinagem ESP32

- GPIO5 - TX CAN
- GPIO4 - RX CAN
- 3.3V - VCC
- GND - GND

## ⚠️ Notas de Segurança

- Use proteção adequada no circuito
- Verifique a tensão do barramento CAN (geralmente 12V)
- Use divisor de tensão se necessário
- Não modifique parâmetros críticos do trator

## 📁 Estrutura do Projeto

```
canbus-monitor/
├── README.md
├── requirements.txt
├── LICENSE
├── src/
│   ├── esp32/
│   │   ├── main.py
│   │   ├── web_server.py
│   │   └── j1939_parser.py
│   └── dashboard/
│       └── dashboard.py
├── docs/
│   └── images/
└── tests/
```

## 📦 Dependências

As principais dependências do projeto estão listadas no arquivo `requirements.txt`:

- streamlit
- pandas
- plotly
- folium
- streamlit-folium
- requests
- mpremote
- esptool

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Faça commit das suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Faça Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ✍️ Autor

Givanildo - [@givanildo](https://github.com/givanildo)

## 🙏 Agradecimentos
- https://github.com/FarmLogs/pysobus
- John Deere pela documentação J1939
- Comunidade MicroPython
- Contribuidores do Streamlit
