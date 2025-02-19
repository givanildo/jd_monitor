import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import folium
from streamlit_folium import st_folium

# Configuração da página
st.set_page_config(
    page_title="Dashboard Trator John Deere",
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
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Título
st.title("🚜 Monitor ISOBUS - Trator John Deere")

# Inicialização do estado da sessão
if 'running' not in st.session_state:
    st.session_state.running = True
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'auto_update' not in st.session_state:
    st.session_state.auto_update = True

# Controles de execução no sidebar
with st.sidebar:
    st.header("⚙️ Controles")
    
    # Botões de controle
    col1, col2 = st.columns(2)
    with col1:
        if st.button('⏹️ Parar'):
            st.session_state.running = False
            st.session_state.auto_update = False
            st.stop()
    with col2:
        if st.button('▶️ Iniciar'):
            st.session_state.running = True
            st.session_state.auto_update = True
            st.rerun()
    
    # Toggle de atualização automática
    st.session_state.auto_update = st.checkbox("Atualização Automática", 
                                             value=st.session_state.auto_update)

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

# Configurações no Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Conexão
    st.subheader("Conexão")
    esp32_ip = st.text_input("IP do ESP32", "192.168.1.100")
    intervalo_atualizacao = st.slider("Intervalo de atualização (s)", 1, 10, 2)
    
    # Filtros
    st.subheader("Filtros")
    periodo = st.selectbox(
        "Período de dados",
        ["Última hora", "Últimas 24 horas", "Última semana", "Tempo real"]
    )
    
    categorias = st.multiselect(
        "Categorias de dados",
        ["Motor", "Posição", "Ambiente", "Implemento"],
        default=["Motor"]
    )
    
    # Filtros avançados
    st.subheader("Filtros Avançados")
    
    # Filtro de período
    periodo_analise = st.selectbox(
        "Período de análise",
        ["Tempo real", "Última hora", "Últimas 24 horas", "Última semana", "Personalizado"]
    )
    
    if periodo_analise == "Personalizado":
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data inicial")
            hora_inicio = st.time_input("Hora inicial")
        with col2:
            data_fim = st.date_input("Data final")
            hora_fim = st.time_input("Hora final")
    
    # Filtros de valores
    st.subheader("Filtros de Valores")
    mostrar_filtros = st.checkbox("Mostrar filtros de valores")
    
    if mostrar_filtros:
        rpm_range = st.slider("Faixa de RPM", 0, 3000, (0, 3000))
        temp_range = st.slider("Faixa de Temperatura", 0, 120, (0, 120))
        pressao_range = st.slider("Faixa de Pressão", 0, 10, (0, 10))
    
    # Configurações de visualização
    st.subheader("Visualização")
    max_pontos = st.slider("Máximo de pontos nos gráficos", 50, 1000, 200)
    tema_graficos = st.selectbox("Tema dos gráficos", ["light", "dark"])
    
    # Botão de atualização manual
    if st.button("🔄 Atualizar Dados"):
        st.session_state.last_update = time.time()

# Função para criar gauge
def criar_gauge(valor, titulo, min_val, max_val, referencia=None):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        title={'text': titulo},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [min_val, max_val*0.3], 'color': "lightgray"},
                {'range': [max_val*0.3, max_val*0.7], 'color': "gray"},
                {'range': [max_val*0.7, max_val], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': referencia if referencia else max_val*0.8
            }
        }
    ))
    fig.update_layout(height=200)
    return fig

# Layout principal em abas
tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "🔧 Motor", "📍 Localização", "📈 Análise"])

# Função para buscar dados
@st.cache_data(ttl=1)
def buscar_dados(ip):
    try:
        response = requests.get(f"http://{ip}/dados", timeout=2)
        return response.json()
    except:
        return None

# Atualização dos dados
current_time = time.time()
if st.session_state.auto_update and (current_time - st.session_state.last_update) >= intervalo_atualizacao:
    st.session_state.last_update = current_time
    dados = buscar_dados(esp32_ip)
else:
    dados = buscar_dados(esp32_ip)

# Tab 1: Visão Geral
with tab1:
    if dados:
        col1, col2, col3 = st.columns(3)
        
        # Métricas principais
        with col1:
            st.metric(
                "RPM do Motor",
                f"{dados['engine_data']['rpm']:.0f}",
                f"{dados['engine_data']['rpm'] - 800:.0f}"
            )
            
            # Gauge de RPM
            st.plotly_chart(
                criar_gauge(
                    dados['engine_data']['rpm'],
                    "RPM",
                    0,
                    3000,
                    2400
                ),
                use_container_width=True
            )
            
        with col2:
            st.metric(
                "Temperatura do Motor",
                f"{dados['engine_data']['coolant_temp']}°C",
                f"{dados['engine_data']['coolant_temp'] - 90:.1f}°C"
            )
            
            # Gauge de Temperatura
            st.plotly_chart(
                criar_gauge(
                    dados['engine_data']['coolant_temp'],
                    "Temperatura °C",
                    0,
                    120,
                    95
                ),
                use_container_width=True
            )
            
        with col3:
            st.metric(
                "Pressão do Óleo",
                f"{dados['engine_data']['oil_pressure']} bar",
                f"{dados['engine_data']['oil_pressure'] - 3:.1f} bar"
            )
            
            # Gauge de Pressão
            st.plotly_chart(
                criar_gauge(
                    dados['engine_data']['oil_pressure'],
                    "Pressão (bar)",
                    0,
                    10,
                    2
                ),
                use_container_width=True
            )
    else:
        st.error("Não foi possível conectar ao ESP32. Verifique o IP e a conexão.")

# Tab 2: Motor
with tab2:
    if "Motor" in categorias and dados:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico histórico de RPM
            if 'historico' in dados and 'motor' in dados['historico']:
                df_motor = pd.DataFrame(dados['historico']['motor'])
                fig_rpm = px.line(
                    df_motor,
                    x='timestamp',
                    y='dados.Engine_Speed',
                    title='Histórico de RPM'
                )
                st.plotly_chart(fig_rpm, use_container_width=True)
        
        with col2:
            # Gráfico de carga do motor
            if 'engine_load' in dados['engine_data']:
                fig_carga = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=dados['engine_data']['engine_load'],
                    title={'text': "Carga do Motor (%)"},
                    gauge={'axis': {'range': [0, 100]}}
                ))
                st.plotly_chart(fig_carga, use_container_width=True)

# Tab 3: Localização
with tab3:
    if "Posição" in categorias and dados:
        # Mapa com histórico de posições
        if 'position_data' in dados:
            pos = dados['position_data']
            if pos.get('latitude') and pos.get('longitude'):
                m = folium.Map(
                    location=[pos['latitude'], pos['longitude']],
                    zoom_start=16
                )
                folium.Marker(
                    [pos['latitude'], pos['longitude']],
                    popup="Trator",
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(m)
                st_folium(m, width=800, height=400)

# Tab 4: Análise
with tab4:
    if dados and 'historico' in dados:
        st.subheader("Análise de Dados")
        
        # Layout em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleção de métricas
            metricas_selecionadas = st.multiselect(
                "Selecione as métricas para análise",
                list(METRICAS.keys()),
                default=["RPM"]
            )
            
            # Tipo de visualização
            tipo_viz = st.selectbox(
                "Tipo de visualização",
                ["Linha", "Dispersão", "Barras", "Box Plot"]
            )
        
        with col2:
            # Agregações
            tipo_agregacao = st.selectbox(
                "Tipo de agregação",
                ["Nenhuma", "Média", "Máximo", "Mínimo", "Mediana"]
            )
            
            # Intervalo de agregação
            if tipo_agregacao != "Nenhuma":
                intervalo_agregacao = st.selectbox(
                    "Intervalo de agregação",
                    ["Minuto", "Hora", "Dia", "Semana"]
                )

        # Processamento dos dados
        try:
            df_analise = pd.DataFrame(dados['historico']['motor'])
            
            # Aplica filtros de período
            df_filtrado = filtrar_dados_por_periodo(df_analise, periodo_analise)
            
            # Aplica filtros de valores se ativados
            if mostrar_filtros:
                df_filtrado = df_filtrado[
                    (df_filtrado['dados.Engine_Speed'].between(*rpm_range)) &
                    (df_filtrado['dados.Engine_Coolant_Temperature'].between(*temp_range)) &
                    (df_filtrado['dados.Engine_Oil_Pressure'].between(*pressao_range))
                ]
            
            # Cria visualizações
            for metrica in metricas_selecionadas:
                coluna_dados = METRICAS[metrica]
                
                if tipo_viz == "Linha":
                    fig = px.line(
                        df_filtrado,
                        x='timestamp',
                        y=coluna_dados,
                        title=f'{metrica} ao longo do tempo'
                    )
                elif tipo_viz == "Dispersão":
                    fig = px.scatter(
                        df_filtrado,
                        x='timestamp',
                        y=coluna_dados,
                        title=f'Dispersão de {metrica}'
                    )
                elif tipo_viz == "Barras":
                    fig = px.bar(
                        df_filtrado,
                        x='timestamp',
                        y=coluna_dados,
                        title=f'Distribuição de {metrica}'
                    )
                elif tipo_viz == "Box Plot":
                    fig = px.box(
                        df_filtrado,
                        y=coluna_dados,
                        title=f'Distribuição de {metrica}'
                    )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas resumidas
            st.subheader("Estatísticas Resumidas")
            stats_df = df_filtrado[[col for col in df_filtrado.columns if 'dados.' in col]].describe()
            st.dataframe(stats_df)
            
            # Download dos dados filtrados
            st.download_button(
                label="📥 Download dos dados filtrados",
                data=df_filtrado.to_csv(index=False),
                file_name="dados_filtrados.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Erro ao processar dados históricos: {e}")

# Atualização automática usando rerun com intervalo
if st.session_state.running and st.session_state.auto_update:
    time.sleep(0.1)  # Pequeno delay para evitar sobrecarga
    st.rerun() 