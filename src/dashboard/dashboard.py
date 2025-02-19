import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import time
import folium
from streamlit_folium import st_folium
from j1939_parser import J1939Parser
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Monitor ISOBUS - John Deere",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .gauge-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        padding: 1rem;
    }
    .status-ok {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .chart-container {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Título
st.title("🚜 Monitor ISOBUS - John Deere")

# Inicialização do estado da sessão
if 'running' not in st.session_state:
    st.session_state.running = True
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'auto_update' not in st.session_state:
    st.session_state.auto_update = True
if 'historic_data' not in st.session_state:
    st.session_state.historic_data = []
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = False
if 'parser' not in st.session_state:
    st.session_state.parser = J1939Parser()

# Inicializa parser
parser = J1939Parser()

# Controles de execução no sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Conexão
    st.subheader("Conexão")
    ip_esp32 = st.text_input("IP do ESP32", "192.168.4.1")
    
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
    
    # Atualização
    st.subheader("Atualização")
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    refresh_rate = st.slider("Taxa (segundos)", 1, 10, 2)
    
    # Filtros
    st.subheader("Visualizações")
    show_engine = st.checkbox("Motor", value=True)
    show_vehicle = st.checkbox("Veículo", value=True)
    show_raw = st.checkbox("Dados Brutos", value=False)

# Configurações de Gauges
GAUGE_CONFIG = {
    'engine': {
        'rpm': {'title': 'RPM', 'min': 0, 'max': 3000, 'unit': 'RPM', 'warning': 2400, 'danger': 2800},
        'coolant_temp': {'title': 'Temperatura', 'min': 0, 'max': 120, 'unit': '°C', 'warning': 95, 'danger': 105},
        'oil_temp': {'title': 'Temp. Óleo', 'min': 0, 'max': 150, 'unit': '°C', 'warning': 110, 'danger': 120},
        'oil_pressure': {'title': 'Pressão Óleo', 'min': 0, 'max': 10, 'unit': 'bar', 'warning': 2, 'danger': 1},
        'fuel_level': {'title': 'Combustível', 'min': 0, 'max': 100, 'unit': '%', 'warning': 20, 'danger': 10},
        'load': {'title': 'Carga', 'min': 0, 'max': 100, 'unit': '%', 'warning': 85, 'danger': 95},
        'boost_pressure': {'title': 'Pressão Turbo', 'min': 0, 'max': 3, 'unit': 'bar', 'warning': 2.5, 'danger': 2.8},
        'fuel_rate': {'title': 'Consumo', 'min': 0, 'max': 100, 'unit': 'L/h', 'warning': 80, 'danger': 90}
    },
    'vehicle': {
        'wheel_speed': {'title': 'Velocidade', 'min': 0, 'max': 40, 'unit': 'km/h', 'warning': 35, 'danger': 38},
        'brake_pressure': {'title': 'Freio', 'min': 0, 'max': 10, 'unit': 'bar', 'warning': 8, 'danger': 9},
        'hydraulic_pressure': {'title': 'Hidráulico', 'min': 0, 'max': 250, 'unit': 'bar', 'warning': 220, 'danger': 240},
        'transmission_temp': {'title': 'Temp. Transmissão', 'min': 0, 'max': 150, 'unit': '°C', 'warning': 110, 'danger': 120}
    }
}

# Filtros Avançados
with st.sidebar:
    st.subheader("🔍 Filtros")
    
    # Seleção de período
    st.markdown("### Período")
    periodo = st.selectbox(
        "Intervalo",
        ["Última Hora", "Últimas 6 Horas", "Último Dia", "Última Semana", "Personalizado"]
    )
    
    if periodo == "Personalizado":
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Início")
        with col2:
            data_fim = st.date_input("Fim")
    
    # Filtros de dados
    st.markdown("### Métricas")
    metricas_selecionadas = st.multiselect(
        "Selecione as métricas",
        list(GAUGE_CONFIG['engine'].keys()) + list(GAUGE_CONFIG['vehicle'].keys()),
        default=['rpm', 'wheel_speed', 'coolant_temp']
    )
    
    # Limites de alerta
    st.markdown("### Limites")
    if metricas_selecionadas:
        for metrica in metricas_selecionadas:
            if metrica in GAUGE_CONFIG['engine']:
                config = GAUGE_CONFIG['engine'][metrica]
            else:
                config = GAUGE_CONFIG['vehicle'][metrica]
                
            st.markdown(f"**{config['title']}**")
            col1, col2 = st.columns(2)
            with col1:
                warning = st.number_input(
                    "Alerta",
                    min_value=float(config['min']),
                    max_value=float(config['max']),
                    value=float(config['warning'])
                )
            with col2:
                danger = st.number_input(
                    "Crítico",
                    min_value=float(config['min']),
                    max_value=float(config['max']),
                    value=float(config['danger'])
                )
            GAUGE_CONFIG['engine' if metrica in GAUGE_CONFIG['engine'] else 'vehicle'][metrica].update({
                'warning': warning,
                'danger': danger
            })

# Adiciona funções de filtragem
def filtrar_dados_por_periodo(df, periodo):
    now = pd.Timestamp.now()
    if periodo == "Última hora":
        return df[df['timestamp'] >= now - pd.Timedelta(hours=1)]
    elif periodo == "Últimas 24 horas":
        return df[df['timestamp'] >= now - pd.Timedelta(days=1)]
    elif periodo == "Última semana":
        return df[df['timestamp'] >= now - pd.Timedelta(weeks=1)]
    return df

def agregar_dados(df, metrica, tipo_agregacao):
    if tipo_agregacao == "Média":
        return df[metrica].mean()
    elif tipo_agregacao == "Máximo":
        return df[metrica].max()
    elif tipo_agregacao == "Mínimo":
        return df[metrica].min()
    return None

# Mapeamento de métricas
METRICAS = {
    "RPM": "dados.Engine_Speed",
    "Temperatura": "dados.Engine_Coolant_Temperature",
    "Pressão do Óleo": "dados.Engine_Oil_Pressure",
    "Carga do Motor": "dados.Engine_Percent_Load"
}

# Função para criar gauge
def create_gauge(value, title, min_val, max_val, unit="", warning=None, danger=None):
    # Define cores baseadas em limites
    if danger and value >= danger:
        color = "red"
    elif warning and value >= warning:
        color = "orange"
    else:
        color = "green"
        
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': f"{title}<br><sub>{unit}</sub>"},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': color},
            'steps': [
                {'range': [min_val, max_val*0.6], 'color': "lightgray"},
                {'range': [max_val*0.6, max_val*0.8], 'color': "gray"},
                {'range': [max_val*0.8, max_val], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': danger if danger else max_val
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#2c3e50", 'family': "Arial"}
    )
    return fig

# Função para criar gráfico de linha
def create_line_chart(df, y_col, title, unit):
    fig = px.line(df, x='timestamp', y=y_col, title=title)
    fig.update_layout(
        yaxis_title=unit,
        xaxis_title="Tempo",
        height=250,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#2c3e50"}
    )
    return fig

# Layout principal em abas
tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🔧 Detalhes", "📈 Análise"])

# Função para gerar dados simulados
def gerar_dados_simulados():
    try:
        return {
            'status': {
                'connected': False,
                'wifi_signal': 0,
                'messages_per_second': 0,
                'errors': 0
            },
            'engine': {
                'rpm': 0,
                'speed': 0,
                'temperature': 0,
                'load': 0,
                'hours': 0,
                'fuel_level': 0,
                'oil_pressure': 0
            },
            'transmission': {
                'gear': 0,
                'ratio': 0
            },
            'hydraulics': {
                'pressure': 0,
                'flow': 0,
                'temperature': 0
            },
            'position': {
                'latitude': 0,
                'longitude': 0,
                'altitude': 0
            }
        }
    except Exception as e:
        st.error(f"Erro ao gerar dados simulados: {str(e)}")
        return None

# Função para buscar dados com tratamento de erros
@st.cache_data(ttl=1)
def buscar_dados(ip):
    """Busca dados do ESP32"""
    try:
        response = requests.get(f"http://{ip}/api/data", timeout=2)
        if response.status_code == 200:
            dados = response.json()
            # Garante que todas as chaves existam
            if 'status' not in dados:
                dados['status'] = {'connected': False, 'messages_per_second': 0, 'errors': 0}
            if 'engine' not in dados:
                dados['engine'] = {}
            if 'vehicle' not in dados:
                dados['vehicle'] = {}
            if 'raw_messages' not in dados:
                dados['raw_messages'] = []
            return dados
    except:
        pass
    
    # Retorna estrutura vazia em caso de erro
    return {
        'status': {'connected': False, 'messages_per_second': 0, 'errors': 0},
        'engine': {},
        'vehicle': {},
        'raw_messages': []
    }

# Atualização dos dados
current_time = time.time()
if st.session_state.auto_update and (current_time - st.session_state.last_update) >= refresh_rate:
    st.session_state.last_update = current_time
    dados = buscar_dados(ip_esp32)
else:
    dados = buscar_dados(ip_esp32)

# Atualiza função process_can_messages
def process_can_messages(messages):
    if not messages:
        return pd.DataFrame()
        
    data = []
    
    for msg in messages:
        parsed = parser.parse_message(msg)
        if parsed:
            data.extend(parsed)
            
    return pd.DataFrame(data)

# Função para filtrar dados por período
def filtrar_dados(df, periodo, inicio=None, fim=None):
    now = pd.Timestamp.now()
    if periodo == "Última Hora":
        return df[df['timestamp'] >= now - pd.Timedelta(hours=1)]
    elif periodo == "Últimas 6 Horas":
        return df[df['timestamp'] >= now - pd.Timedelta(hours=6)]
    elif periodo == "Último Dia":
        return df[df['timestamp'] >= now - pd.Timedelta(days=1)]
    elif periodo == "Última Semana":
        return df[df['timestamp'] >= now - pd.Timedelta(weeks=1)]
    elif periodo == "Personalizado" and inicio and fim:
        return df[(df['timestamp'].dt.date >= inicio) & (df['timestamp'].dt.date <= fim)]
    return df

# Tab 1: Visão Geral
with tab1:
    # Status
    st.subheader("Status do Sistema")
    status_cols = st.columns(4)
    
    # Busca dados uma vez para usar em toda a interface
    dados = buscar_dados(ip_esp32)
    
    if dados:
        with status_cols[0]:
            status = "CONECTADO" if dados.get('status', {}).get('connected', False) else "DESCONECTADO"
            st.metric("Status", status)
        with status_cols[1]:
            signal = dados.get('status', {}).get('wifi_signal', 0)
            st.metric("Sinal WiFi", f"{signal} dBm")
        with status_cols[2]:
            msgs = dados.get('status', {}).get('messages_per_second', 0)
            st.metric("Mensagens/s", str(msgs))
        with status_cols[3]:
            erros = dados.get('status', {}).get('errors', 0)
            st.metric("Erros", str(erros))
        
        # Gauges dinâmicos baseados na seleção
        if dados:
            st.subheader("Motor e Veículo")
            
            # Organiza gauges em linhas de 4
            n_cols = 4
            metricas_chunks = [metricas_selecionadas[i:i + n_cols] for i in range(0, len(metricas_selecionadas), n_cols)]
            
            for chunk in metricas_chunks:
                cols = st.columns(n_cols)
                for i, metrica in enumerate(chunk):
                    with cols[i]:
                        if metrica in GAUGE_CONFIG['engine']:
                            config = GAUGE_CONFIG['engine'][metrica]
                            valor = dados.get('engine', {}).get(metrica, 0)
                        else:
                            config = GAUGE_CONFIG['vehicle'][metrica]
                            valor = dados.get('vehicle', {}).get(metrica, 0)
                            
                        st.plotly_chart(create_gauge(
                            valor,
                            config['title'],
                            config['min'],
                            config['max'],
                            config['unit'],
                            config['warning'],
                            config['danger']
                        ), use_container_width=True)
        
        # Histórico filtrado
        if st.session_state.historic_data:
            df_historic = pd.DataFrame(st.session_state.historic_data)
            df_filtered = filtrar_dados(
                df_historic,
                periodo,
                data_inicio if periodo == "Personalizado" else None,
                data_fim if periodo == "Personalizado" else None
            )
            
            # Gráficos das métricas selecionadas
            st.subheader("Histórico")
            for i in range(0, len(metricas_selecionadas), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(metricas_selecionadas):
                        metrica = metricas_selecionadas[i + j]
                        col_name = f"{'engine' if metrica in GAUGE_CONFIG['engine'] else 'vehicle'}_{metrica}"
                        if col_name in df_filtered.columns:
                            with cols[j]:
                                config = GAUGE_CONFIG['engine' if metrica in GAUGE_CONFIG['engine'] else 'vehicle'][metrica]
                                st.plotly_chart(create_line_chart(
                                    df_filtered,
                                    col_name,
                                    config['title'],
                                    config['unit']
                                ), use_container_width=True)
    else:
        st.error("Não foi possível obter dados do sistema")

# Tab 2: Detalhes
with tab2:
    st.subheader("Dados Detalhados do Motor")
    detail_cols = st.columns(2)
    
    if dados:
        with detail_cols[0]:
            # Métricas detalhadas
            st.markdown("### Motor")
            motor_cols = st.columns(2)
            with motor_cols[0]:
                torque = dados.get('engine', {}).get('torque', 0)
                power = dados.get('engine', {}).get('power', 0)
                st.metric("Torque", f"{torque} Nm")
                st.metric("Potência", f"{power} HP")
            with motor_cols[1]:
                consumption = dados.get('engine', {}).get('fuel_rate', 0)
                oil_temp = dados.get('engine', {}).get('oil_temperature', 0)
                st.metric("Consumo", f"{consumption} L/h")
                st.metric("Temp. Óleo", f"{oil_temp}°C")
        
        with detail_cols[1]:
            # Gráfico de torque x rpm
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[800, 1200, 1600, 2000, 2400, 2800],
                y=[300, 400, 450, 440, 380, 320],
                name="Torque"
            ))
            fig.update_layout(
                title="Curva de Torque",
                xaxis_title="RPM",
                yaxis_title="Torque (Nm)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Dados não disponíveis")

# Tab 3: Análise
with tab3:
    st.subheader("Análise de Desempenho")
    
    if dados:
        # Filtros de tempo
        time_filter = st.selectbox(
            "Período de Análise",
            ["Última Hora", "Último Dia", "Última Semana", "Último Mês"]
        )
        
        # Métricas de desempenho
        perf_cols = st.columns(4)
        with perf_cols[0]:
            hours = dados.get('engine', {}).get('hours', 0)
            st.metric("Horas Motor", f"{hours:.1f} h")
        with perf_cols[1]:
            avg_consumption = dados.get('engine', {}).get('average_consumption', 0)
            st.metric("Consumo Médio", f"{avg_consumption:.1f} L/h")
        with perf_cols[2]:
            distance = dados.get('position', {}).get('distance', 0)
            st.metric("Distância", f"{distance:.1f} km")
        with perf_cols[3]:
            productivity = dados.get('engine', {}).get('productivity', 0)
            st.metric("Produtividade", f"{productivity:.0%}")
        
        # Gráficos de análise
        st.markdown("### Análise de Tendências")
        trend_cols = st.columns(2)
        
        with trend_cols[0]:
            # Gráfico de consumo ao longo do tempo (usando 'h' em vez de 'H')
            df_consumo = pd.DataFrame({
                'timestamp': pd.date_range(start='now', periods=24, freq='h'),
                'consumo': np.random.normal(avg_consumption, 2, 24)
            })
            st.plotly_chart(create_line_chart(
                df_consumo, 'consumo', 'Consumo por Hora', 'L/h'
            ), use_container_width=True)
        
        with trend_cols[1]:
            # Gráfico de carga do motor (usando 'h' em vez de 'H')
            engine_load = dados.get('engine', {}).get('load', 50)
            df_carga = pd.DataFrame({
                'timestamp': pd.date_range(start='now', periods=24, freq='h'),
                'carga': np.random.normal(engine_load, 10, 24)
            })
            st.plotly_chart(create_line_chart(
                df_carga, 'carga', 'Carga do Motor', '%'
            ), use_container_width=True)
    else:
        st.error("Dados não disponíveis")

# Atualização automática usando rerun com intervalo
if st.session_state.running and st.session_state.auto_update:
    time.sleep(0.1)  # Pequeno delay para evitar sobrecarga
    st.rerun() 