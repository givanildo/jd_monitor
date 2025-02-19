import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import folium
from streamlit_folium import st_folium
from j1939_parser import J1939Parser

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Dashboard Trator John Deere ISOBUS",
    page_icon="🚜",
    layout="wide"
)

# Título do dashboard
st.title("🚜 Monitor ISOBUS - Trator John Deere")

# Inicialização do estado da sessão
if 'dados_historicos' not in st.session_state:
    st.session_state.dados_historicos = pd.DataFrame()
if 'parser' not in st.session_state:
    st.session_state.parser = J1939Parser()

# Configurações no sidebar
with st.sidebar:
    st.header("Configurações")
    esp32_ip = st.text_input("IP do ESP32", "192.168.4.1")
    intervalo_atualizacao = st.slider("Intervalo de atualização (s)", 1, 10, 2)
    max_pontos = st.slider("Máximo de pontos no gráfico", 50, 500, 100)

# Layout em três colunas
col1, col2, col3 = st.columns([2, 2, 1])

# Função para buscar dados do ESP32
def buscar_dados_esp32(url):
    try:
        response = requests.get(f"http://{url}/api/data", timeout=2)
        return response.json()
    except:
        return None

# Criação dos placeholders para atualização
with col1:
    st.subheader("Dados do Motor")
    motor_metrics = st.empty()
    rpm_chart = st.empty()

with col2:
    st.subheader("Localização")
    mapa = st.empty()
    
with col3:
    st.subheader("Dados de Implemento")
    implemento_info = st.empty()
    st.subheader("Dados de Produtividade")
    yield_info = st.empty()

# Função para atualizar o dashboard
def atualizar_dashboard():
    dados = buscar_dados_esp32(esp32_ip)
    if dados:
        # Atualiza métricas do motor
        engine_data = dados.get('engine', {})
        with motor_metrics:
            cols = st.columns(2)
            with cols[0]:
                st.metric("RPM", f"{engine_data.get('engine_speed', 0):.0f}")
                st.metric("Carga", f"{engine_data.get('load', 0):.1f}%")
            with cols[1]:
                st.metric("Consumo", f"{engine_data.get('fuel_rate', 0):.1f} L/h")
                st.metric("Temperatura", f"{engine_data.get('coolant_temp', 0)}°C")
            
        # Atualiza histórico
        if len(st.session_state.dados_historicos) > max_pontos:
            st.session_state.dados_historicos = st.session_state.dados_historicos.iloc[-max_pontos:]
        
        # Gráfico de RPM
        with rpm_chart:
            fig = px.line(st.session_state.dados_historicos, 
                         x='timestamp', 
                         y='engine_speed',
                         title='RPM do Motor')
            st.plotly_chart(fig, use_container_width=True)

# Loop principal de atualização
if st.sidebar.button("Iniciar Monitoramento"):
    while True:
        atualizar_dashboard()
        time.sleep(intervalo_atualizacao)