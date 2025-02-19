import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import folium
from streamlit_folium import st_folium

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

# Configurações no sidebar
with st.sidebar:
    st.header("Configurações")
    esp32_ip = st.text_input("IP do ESP32", "192.168.1.100")
    intervalo_atualizacao = st.slider("Intervalo de atualização (s)", 1, 10, 2)
    max_pontos = st.slider("Máximo de pontos no gráfico", 50, 500, 100)

# Layout em três colunas
col1, col2, col3 = st.columns([2, 2, 1])

# Função para buscar dados do ESP32
def buscar_dados_esp32(url):
    try:
        response = requests.get(f"http://{url}", timeout=2)
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
        engine_data = dados['engine_data']
        with col1:
            motor_metrics.columns([
                dict(
                    metric="RPM",
                    value=f"{engine_data.get('rpm', 0):.0f}",
                    delta=f"{engine_data.get('load', 0):.1f}%"
                ),
                dict(
                    metric="Consumo",
                    value=f"{engine_data.get('fuel_rate', 0):.1f} L/h"
                )
            ])
            
            # Gráfico de RPM histórico
            if 'historico' in dados:
                df_hist = pd.DataFrame(dados['historico'])
                fig_rpm = px.line(df_hist, x='timestamp', y='valores.Engine_Speed',
                                title='RPM do Motor')
                rpm_chart.plotly_chart(fig_rpm, use_container_width=True)
        
        # Atualiza mapa
        position_data = dados['position_data']
        if position_data.get('latitude') and position_data.get('longitude'):
            m = folium.Map(
                location=[position_data['latitude'], position_data['longitude']],
                zoom_start=16
            )
            folium.Marker(
                [position_data['latitude'], position_data['longitude']],
                popup="Trator",
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)
            mapa.empty()
            st_folium(m, width=400, height=300)
        
        # Atualiza dados do implemento
        implement_data = dados['implement_data']
        implemento_info.json(implement_data)
        
        # Atualiza dados de produtividade
        yield_data = dados['yield_data']
        yield_info.json(yield_data)

# Loop principal de atualização
while True:
    atualizar_dashboard()
    time.sleep(intervalo_atualizacao)