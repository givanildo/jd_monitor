import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import folium
from streamlit_folium import st_folium
from src.esp32.isobus.j1939_parser import J1939Parser

# Classe principal do dashboard
class Dashboard:
    def __init__(self):
        self.setup_page()
        self.init_session_state()
        self.setup_sidebar()
        
    def setup_page(self):
        st.set_page_config(
            page_title="Monitor ISOBUS - John Deere",
            page_icon="🚜",
            layout="wide"
        )
        st.title("🚜 Monitor ISOBUS - John Deere")
        
    def init_session_state(self):
        if 'dados_historicos' not in st.session_state:
            st.session_state.dados_historicos = pd.DataFrame()
        if 'parser' not in st.session_state:
            st.session_state.parser = J1939Parser()
            
    def setup_sidebar(self):
        with st.sidebar:
            st.header("Configurações")
            self.esp32_ip = st.text_input("IP do ESP32", "192.168.4.1")
            self.intervalo = st.slider("Atualização (s)", 1, 10, 2)
            self.max_pontos = st.slider("Máx. pontos", 50, 500, 100)
            
    def run(self):
        if st.sidebar.button("Iniciar Monitoramento"):
            while True:
                self.update_dashboard()
                time.sleep(self.intervalo)
                
    def update_dashboard(self):
        dados = self.get_data()
        if dados:
            self.show_metrics(dados)
            self.update_charts(dados)
            
    def get_data(self):
        try:
            response = requests.get(
                f"http://{self.esp32_ip}/api/data", 
                timeout=2
            )
            return response.json()
        except:
            return None
            
    def show_metrics(self, dados):
        cols = st.columns(4)
        engine = dados.get('engine', {})
        
        with cols[0]:
            st.metric("RPM", f"{engine.get('engine_speed', 0):.0f}")
        with cols[1]:
            st.metric("Temperatura", f"{engine.get('coolant_temp', 0)}°C")
        with cols[2]:
            st.metric("Consumo", f"{engine.get('fuel_rate', 0):.1f} L/h")
        with cols[3]:
            st.metric("Carga", f"{engine.get('load', 0):.1f}%")
            
    def update_charts(self, dados):
        # Atualiza histórico
        if len(st.session_state.dados_historicos) > self.max_pontos:
            st.session_state.dados_historicos = (
                st.session_state.dados_historicos.iloc[-self.max_pontos:]
            )
        
        # Gráfico RPM
        fig = px.line(
            st.session_state.dados_historicos,
            x='timestamp',
            y='engine_speed',
            title='RPM do Motor'
        )
        st.plotly_chart(fig, use_container_width=True)

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