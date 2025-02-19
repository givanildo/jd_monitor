import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
import time
from datetime import datetime
import numpy as np

# Configurações da página
st.set_page_config(
    page_title="JD Monitor Dashboard",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa variáveis de estado
if 'historic_data' not in st.session_state:
    st.session_state.historic_data = []
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = False

# Estilo CSS customizado
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .gauge-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .status-connected {
        color: green;
        font-weight: bold;
    }
    .status-disconnected {
        color: red;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.title("🚜 John Deere Monitor Dashboard")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    ip_esp32 = st.text_input("IP do ESP32", "192.168.4.1")
    
    # Teste de conexão
    if st.button("Testar Conexão"):
        try:
            response = requests.get(f"http://{ip_esp32}/api/data", timeout=3)
            if response.status_code == 200:
                st.success("Conexão estabelecida!")
                st.session_state.connection_status = True
            else:
                st.error("Erro na conexão")
                st.session_state.connection_status = False
        except:
            st.error("Não foi possível conectar")
            st.session_state.connection_status = False
    
    st.markdown("---")
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    refresh_rate = st.slider("Taxa de Atualização (s)", 1, 10, 2)
    
    st.markdown("---")
    st.subheader("Visualizações")
    show_rpm = st.checkbox("RPM do Motor", value=True)
    show_speed = st.checkbox("Velocidade", value=True)
    show_temp = st.checkbox("Temperatura", value=True)
    show_fuel = st.checkbox("Combustível", value=True)
    show_load = st.checkbox("Carga do Motor", value=True)

# Função para criar gauge com dados simulados para teste
def create_gauge(value, title, min_val, max_val, suffix=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 24}},
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': suffix, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1},
            'bar': {'color': "#2ecc71"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [min_val, max_val*0.33], 'color': '#ff9999'},
                {'range': [max_val*0.33, max_val*0.66], 'color': '#ffff99'},
                {'range': [max_val*0.66, max_val], 'color': '#99ff99'}
            ],
        }
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#2c3e50", 'family': "Arial"}
    )
    return fig

# Função para buscar dados do ESP32 com simulação para teste
def get_can_data(ip):
    try:
        response = requests.get(f"http://{ip}/api/data", timeout=3)
        if response.status_code == 200:
            return response.json()
    except:
        # Dados simulados para teste
        if st.session_state.get('test_mode', True):
            return {
                'wifi_ssid': 'TEST_NETWORK',
                'wifi_ip': ip,
                'wifi_signal': -65,
                'can_messages': [
                    f"ID: 0xCF00400 Data: {format(int(np.random.normal(1500, 300)), '04x')}",
                    f"ID: 0xCF00500 Data: {format(int(np.random.normal(30, 5)), '04x')}",
                    f"ID: 0xCFEE600 Data: {format(int(np.random.normal(90, 10)), '04x')}",
                    f"ID: 0xCF00700 Data: {format(int(np.random.normal(75, 15)), '04x')}",
                    f"ID: 0xCF00800 Data: {format(int(np.random.normal(60, 20)), '04x')}"
                ]
            }
    return None

def process_can_messages(messages):
    if not messages:
        return pd.DataFrame()
    
    data = []
    current_time = datetime.now()
    
    for msg in messages:
        try:
            id_hex = msg.split("ID: ")[1].split(" Data:")[0]
            data_hex = msg.split("Data: ")[1].strip()
            
            can_id = int(id_hex, 16)
            can_data = bytes.fromhex(data_hex)
            
            if can_id == 0xCF00400:  # RPM
                value = int.from_bytes(can_data, 'big') * 0.125
                data.append({"timestamp": current_time, "tipo": "RPM", "valor": value})
                
            elif can_id == 0xCF00500:  # Velocidade
                value = int.from_bytes(can_data, 'big') * 0.1
                data.append({"timestamp": current_time, "tipo": "Velocidade", "valor": value})
                
            elif can_id == 0xCFEE600:  # Temperatura
                value = int.from_bytes(can_data, 'big') - 40
                data.append({"timestamp": current_time, "tipo": "Temperatura", "valor": value})
                
            elif can_id == 0xCF00700:  # Combustível
                value = int.from_bytes(can_data, 'big') * 0.4
                data.append({"timestamp": current_time, "tipo": "Combustível", "valor": value})
                
            elif can_id == 0xCF00800:  # Carga
                value = int.from_bytes(can_data, 'big') * 0.4
                data.append({"timestamp": current_time, "tipo": "Carga", "valor": value})
        except:
            continue
    
    return pd.DataFrame(data)

def update_dashboard():
    data = get_can_data(ip_esp32)
    
    if data:
        # Status da Conexão
        cols_status = st.columns([1,1,1])
        with cols_status[0]:
            st.metric("Status", "CONECTADO" if st.session_state.connection_status else "DESCONECTADO")
        with cols_status[1]:
            st.metric("IP", data['wifi_ip'])
        with cols_status[2]:
            st.metric("Sinal WiFi", f"{data['wifi_signal']} dBm")

        # Processa dados
        df = process_can_messages(data['can_messages'])
        if not df.empty:
            st.session_state.historic_data.append(df)
            if len(st.session_state.historic_data) > 100:
                st.session_state.historic_data.pop(0)
            
            # Combina dados históricos
            df_historic = pd.concat(st.session_state.historic_data)
            
            # Gauges
            st.markdown("### Medidores em Tempo Real")
            gauge_cols = st.columns(3)
            
            if show_rpm:
                with gauge_cols[0]:
                    rpm_value = df[df['tipo'] == 'RPM']['valor'].iloc[-1] if not df[df['tipo'] == 'RPM'].empty else 0
                    st.plotly_chart(create_gauge(rpm_value, "RPM do Motor", 0, 3000, " RPM"), use_container_width=True)
            
            if show_speed:
                with gauge_cols[1]:
                    speed_value = df[df['tipo'] == 'Velocidade']['valor'].iloc[-1] if not df[df['tipo'] == 'Velocidade'].empty else 0
                    st.plotly_chart(create_gauge(speed_value, "Velocidade", 0, 40, " km/h"), use_container_width=True)
            
            if show_temp:
                with gauge_cols[2]:
                    temp_value = df[df['tipo'] == 'Temperatura']['valor'].iloc[-1] if not df[df['tipo'] == 'Temperatura'].empty else 0
                    st.plotly_chart(create_gauge(temp_value, "Temperatura", 0, 120, " °C"), use_container_width=True)

            # Gráficos de Linha
            st.markdown("### Histórico")
            chart_cols = st.columns(2)
            
            with chart_cols[0]:
                if show_fuel:
                    fuel_data = df_historic[df_historic['tipo'] == 'Combustível']
                    if not fuel_data.empty:
                        fig = px.line(fuel_data, x='timestamp', y='valor', 
                                    title='Nível de Combustível',
                                    labels={'valor': '%', 'timestamp': 'Tempo'})
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
            
            with chart_cols[1]:
                if show_load:
                    load_data = df_historic[df_historic['tipo'] == 'Carga']
                    if not load_data.empty:
                        fig = px.line(load_data, x='timestamp', y='valor',
                                    title='Carga do Motor',
                                    labels={'valor': '%', 'timestamp': 'Tempo'})
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)

            # Terminal CAN
            with st.expander("Terminal CAN"):
                for msg in data['can_messages']:
                    st.code(msg)
    else:
        st.error("Sem conexão com o ESP32")

# Loop principal
if auto_refresh:
    placeholder = st.empty()
    with placeholder.container():
        update_dashboard()
    time.sleep(refresh_rate)
    st.rerun()
else:
    if st.button("Atualizar"):
        update_dashboard() 