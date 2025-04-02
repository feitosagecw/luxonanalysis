import streamlit as st
import pandas as pd
import time
from google.cloud import bigquery
from google.auth import default
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from pathlib import Path
import os
from src.sql_manager import SQLManager

# Funções de formatação
def format_float(x):
    """Formata um número float para o padrão brasileiro."""
    try:
        return f"{x:,.2f}".replace(",", "temp").replace(".", ",").replace("temp", ".")
    except Exception:
        return x

def format_brl(x):
    """Formata um número para o padrão monetário brasileiro."""
    try:
        return f"R$ {x:,.2f}".replace(",", "temp").replace(".", ",").replace("temp", ".")
    except Exception:
        return x

def format_percent(x):
    """Formata um número para o padrão percentual brasileiro."""
    try:
        return f"{x:,.2f}%".replace(",", "temp").replace(".", ",").replace("temp", ".")
    except Exception:
        return x

def clean_session_state():
    """Limpa os dados armazenados no session_state após a conclusão da análise."""
    keys_to_clean = [
        'dataset',
        'df_contact_info',
        'df_card_transactions',
        'client_info',
        'df_blocked',
        'blocked_summary',
        'top_cash_in',
        'top_cash_out'
    ]
    
    for key in keys_to_clean:
        if key in st.session_state:
            del st.session_state[key]
    
    # Limpar variáveis de controle
    if 'should_analyze' in st.session_state:
        st.session_state.should_analyze = False
    if 'analysis_done' in st.session_state:
        st.session_state.analysis_done = False

def clean_temp_files():
    """Limpa arquivos temporários e cache."""
    try:
        # Limpar cache do Streamlit
        cache_dir = Path.home() / '.streamlit' / 'cache'
        if cache_dir.exists():
            for file in cache_dir.glob('*'):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Erro ao deletar {file}: {e}")
        
        # Limpar arquivos temporários do BigQuery
        temp_dir = Path.home() / '.bigquery' / 'temp'
        if temp_dir.exists():
            for file in temp_dir.glob('*'):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Erro ao deletar {file}: {e}")
        
        # Limpar arquivos temporários do pandas
        temp_dir = Path.home() / '.pandas' / 'temp'
        if temp_dir.exists():
            for file in temp_dir.glob('*'):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Erro ao deletar {file}: {e}")
        
        return True
    except Exception as e:
        print(f"Erro ao limpar arquivos temporários: {e}")
        return False

# Configuração da página
st.set_page_config(
    page_title="Lux",
    page_icon="src/images/stars_icon_shapes_v2/solid/10.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# Definir o tema como light
st.markdown("""
    <style>
    /* Definir o tema como light */
    :root {
        --background-color: #ffffff;
        --text-color: #1e293b;
    }
    
    /* Estilo para o sidebar com gradiente preto para cinza */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, 
            #1a1a1a 0%, 
            #1a1a1a 33.33%, 
            #ffffff 33.33%, 
            #ffffff 66.66%, 
            #4a4a4a 66.66%, 
            #4a4a4a 100%
        );
    }
    
    /* Ajuste das cores do texto no sidebar para melhor contraste */
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o título no sidebar */
    [data-testid="stSidebar"] h1 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Estilo para labels no sidebar */
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Estilo para o input de texto no sidebar */
    [data-testid="stTextInput"] input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: black !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    [data-testid="stTextInput"] input:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
    }
    
    /* Estilo para o expander no sidebar */
    [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Estilo para os checkboxes no sidebar */
    [data-testid="stCheckbox"] {
        color: white !important;
    }
    
    /* Estilo para o botão no sidebar */
    .stButton > button {
        background: #fdfefb !important;
        color: black !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton > button:hover {
        background: #0c1004 !important;
        color: white !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Estilo para o texto do expander no sidebar */
    [data-testid="stExpander"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o texto do checkbox no sidebar */
    [data-testid="stCheckbox"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o texto do radio no sidebar */
    [data-testid="stRadio"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o texto do selectbox no sidebar */
    [data-testid="stSelectbox"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o texto do text input no sidebar */
    [data-testid="stTextInput"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o texto do button no sidebar */
    [data-testid="stButton"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o texto do divider no sidebar */
    [data-testid="stDivider"] [data-testid="stMarkdown"] {
        color: white !important;
    }
    
    /* Estilo para o texto do expander header no sidebar */
    .streamlit-expanderHeader {
        color: white !important;
    }
    
    /* Estilo específico para o título do expander "Filtro de Transações" - seletor mais específico */
    div[data-testid="stExpander"] > div > div > div > span {
        color: white !important;
    }
    
    /* Estilo específico para o título do expander "Filtro de Transações" - seletor direto */
    .streamlit-expanderHeader {
        color: white !important;
    }
    
    /* Estilo específico para o título do expander "Filtro de Transações" - seletor direto para o texto */
    .streamlit-expanderHeader p {
        color: white !important;
    }
    
    /* Estilo específico para o título do expander "Filtro de Transações" - seletor direto para o texto */
    .streamlit-expanderHeader div {
        color: white !important;
    }
    
    /* Estilo para o texto do expander content no sidebar */
    [data-testid="stExpander"] .streamlit-expanderContent {
        background-color: white !important;
    }
    
    /* Estilo para o texto do checkbox label no sidebar */
    [data-testid="stCheckbox"] .stCheckbox {
        color: white !important;
    }
    
    /* Estilo para o texto do radio label no sidebar */
    [data-testid="stRadio"] .stRadio {
        color: white !important;
    }
    
    /* Estilo para o texto do selectbox label no sidebar */
    [data-testid="stSelectbox"] .stSelectbox {
        color: white !important;
    }
    
    /* Estilo para o texto do text input label no sidebar */
    [data-testid="stTextInput"] .stTextInput {
        color: white !important;
    }
    
    /* Estilo para o texto do button label no sidebar */
    [data-testid="stButton"] .stButton {
        color: white !important;
    }
    
    /* Estilo para o texto do divider label no sidebar */
    [data-testid="stDivider"] .stDivider {
        color: white !important;
    }
    
    /* Estilo para o texto do expander content no sidebar - segunda coluna */
    [data-testid="stExpander"] .streamlit-expanderContent {
        background-color: white !important;
        color: black !important;
    }
    
    /* Estilo para o texto do checkbox label no sidebar - segunda coluna */
    [data-testid="stCheckbox"] .stCheckbox {
        color: black !important;
    }
    
    /* Estilo para o texto do radio label no sidebar - segunda coluna */
    [data-testid="stRadio"] .stRadio {
        color: black !important;
    }
    
    /* Estilo para o texto do selectbox label no sidebar - segunda coluna */
    [data-testid="stSelectbox"] .stSelectbox {
        color: black !important;
    }
    
    /* Estilo para o texto do text input label no sidebar - segunda coluna */
    [data-testid="stTextInput"] .stTextInput {
        color: black !important;
    }
    
    /* Estilo para o texto do button label no sidebar - segunda coluna */
    [data-testid="stButton"] .stButton {
        color: black !important;
    }
    
    /* Estilo para o texto do divider label no sidebar - segunda coluna */
    [data-testid="stDivider"] .stDivider {
        color: black !important;
    }
    
    /* Fundo com gradiente mais suave e moderno */
    body {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        font-family: 'Inter', sans-serif;
        color: #1e293b;
    }
    
    /* Títulos com efeito mais moderno */
    .title {
        font-size: 3.2em;
        font-weight: 800;
        color: #1e293b;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        margin-bottom: 30px;
        letter-spacing: -0.5px;
    }

    .title:hover {
        transform: translateY(-2px);
        text-shadow: 3px 3px 6px rgba(0,0,0,0.15);
    }

    .subheader {
        font-size: 2em;
        font-weight: 600;
        color: #334155;
        margin-bottom: 1em;
        letter-spacing: -0.3px;
    }

    /* Mensagens com ícones e cores mais suaves */
    .st-success { 
        color: #059669; 
        font-weight: 600;
        padding: 12px;
        border-radius: 8px;
        background-color: #ecfdf5;
    }
    
    .st-error { 
        color: #dc2626; 
        font-weight: 600;
        padding: 12px;
        border-radius: 8px;
        background-color: #fef2f2;
    }
    
    .st-warning { 
        color: #d97706; 
        font-weight: 600;
        padding: 12px;
        border-radius: 8px;
        background-color: #fffbeb;
    }

    /* Tabelas mais modernas */
    .css-1oe6wyx, .css-1oe6wyx table {
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        font-size: 0.95em;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        overflow: hidden;
    }

    .css-1oe6wyx th, .css-1oe6wyx td {
        border: none;
        padding: 16px;
        text-align: left;
    }

    .css-1oe6wyx th {
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85em;
        letter-spacing: 0.5px;
    }

    .css-1oe6wyx tr:nth-child(even) {
        background-color: #f8fafc;
    }

    .css-1oe6wyx tr:hover {
        background-color: #f1f5f9;
    }

    /* Barra de progresso mais moderna */
    .stProgress > div > div {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        border-radius: 4px;
    }

    /* Cards de dados mais modernos */
    .dataframe {
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        overflow: hidden;
    }

    /* Gráficos mais modernos */
    .js-plotly-plot {
        border-radius: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializar variáveis do session_state se não existirem
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'sort_input_sidebar' not in st.session_state:
    st.session_state.sort_input_sidebar = "Valor Pix (num)"
if 'show_pep' not in st.session_state:
    st.session_state.show_pep = False
if 'show_corporate_cards' not in st.session_state:
    st.session_state.show_corporate_cards = False

# Inicializar o session_state para o dataset se não existir
if 'dataset' not in st.session_state:
    st.session_state.dataset = None

# Barra de progresso com estilo personalizado
progress_bar = st.progress(0)

# Inicializar o gerenciador de SQL
sql_manager = SQLManager()

# Menu Sidebar
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; margin-bottom: 30px;'>
            <h1 style='color: #1e293b;'> Lux</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Campo de entrada para o ID do Cliente com ícone e placeholder
    id_cliente_str = st.text_input("ID do Cliente:", placeholder="Digite o ID para análise", key="id_cliente_input")
    
    # Adicionar espaçamento antes do expander
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    
    # Menu expansível para filtros (agora abaixo do campo de entrada)
    with st.expander("Filtro de Transações", expanded=False):
        # Adicionar estilo personalizado para o título do expander e background
        st.markdown("""
            <style>
            /* Estilo específico para o título do expander "Filtro de Transações" */
            .streamlit-expanderHeader {
                color: white !important;
            }
            
            /* Estilo para o background do expander */
            [data-testid="stExpander"] {
                background-color: #f8fafc !important;
            }
            
            /* Estilo para o conteúdo do expander */
            [data-testid="stExpander"] .streamlit-expanderContent {
                background-color: #f8fafc !important;
            }
            
            /* Estilo para o texto dentro do expander */
            [data-testid="stExpander"] .streamlit-expanderContent label {
                color: #1e293b !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.session_state.show_pep = st.checkbox("PEP", value=st.session_state.show_pep)
        st.session_state.show_corporate_cards = st.checkbox("Cartões Corporativos", value=st.session_state.show_corporate_cards)
    
    # Adicionar espaçamento antes do botão
    st.markdown("<div style='height: 240px;'></div>", unsafe_allow_html=True)
    
    # Adicionar um separador visual
    st.markdown("<hr style='border: 1px solid rgba(179, 163, 17, 0.1); margin: 20px 0;'>", unsafe_allow_html=True)
    
    # Criar um container fixo para o botão na terceira coluna
    button_container = st.container()
    with button_container:
        # Botão de análise no sidebar - agora na terceira coluna
        if st.button("Analisar 🔍 ", key="analyze_button", use_container_width=True):
            if id_cliente_str:
                try:
                    id_client = int(id_cliente_str)
                except ValueError:
                    st.error("❌ Por favor, insira um ID numérico válido.")
                else:
                    st.session_state.id_client = id_client
                    st.session_state.should_analyze = True
            else:
                st.warning("Por favor, insira um ID do cliente.")
    
    # Se a análise já foi feita, mostrar os filtros
    if 'analysis_done' in st.session_state and st.session_state.analysis_done:
        st.markdown("""
            <div style='color: #1e293b; margin-bottom: 15px;'>
                <h4>🔍 Filtros</h4>
            </div>
        """, unsafe_allow_html=True)

# Título com ícone e subtítulo mais informativo
st.markdown("<div class='subheader'>Overview</div>", unsafe_allow_html=True)

# Adicionar uma descrição mais detalhada
st.markdown("""
    <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 30px;'>
        <h3 style='color: #1e293b; margin-bottom: 10px;'>ℹ️ Sobre a Análise</h3>
        <p style='color:rgb(40, 48, 60); line-height: 1.6;'>
            Esta ferramenta permite analisar detalhadamente as transações de um cliente, incluindo:
        </p>
        <ul style='color: #475569; line-height: 1.6;'>
            <li>Concentração de transações PIX</li>
            <li>Análise de transações em horários atípicos</li>
            <li>Transações com cartões</li>
            <li>Identificação de padrões suspeitos</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# Se a análise foi solicitada, executar
if 'should_analyze' in st.session_state and st.session_state.should_analyze:
    id_client = st.session_state.id_client
    st.info(f"Iniciando análise para o cliente: {id_client} 🔎")
    progress_bar.progress(10)
            
    # Conectar ao BigQuery
    creds, _ = default()
    client = bigquery.Client(project="infinitepay-production")
            
    # Definir a consulta de informações do usuário
    try:
        query_user = sql_manager.get_user_info_query(id_client)
        query_job_user = client.query(query_user)
        client_info = query_job_user.result().to_dataframe()
        st.success("Consulta de informações do cliente concluída com sucesso! ✅")
    except Exception as e:
        st.error(f"Erro ao executar a consulta de informações do cliente: {e}")
        client_info = None
    progress_bar.progress(20)
            
    if client_info is not None and not client_info.empty:
        client_name = client_info.iloc[0]['nome_cliente']
        client_age = client_info.iloc[0]['idade']
        client_status = client_info.iloc[0]['status']
            
        # Exibir informações do cliente
        st.markdown(f"""
            <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
                <h3 style='color: #1e293b; margin-bottom: 15px;'>👤 Informações do Cliente</h3>
                <ul style='color: #475569; line-height: 1.6;'>
                    <li><strong>Nome:</strong> {client_name}</li>
                    <li><strong>Idade:</strong> {client_age} anos</li>
                    <li><strong>Status:</strong> {client_status}</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Nenhum dado de cliente foi retornado. Verifique o ID do cliente e tente novamente.")

    # Consulta Pix Concentração
    try:
        query_pix = sql_manager.get_pix_concentration_query(id_client)
        query_job = client.query(query_pix)
        dataset = query_job.result().to_dataframe()
        st.success("Consulta Pix concluída com sucesso! ✅")
    except Exception as e:
        st.error(f"Erro ao executar a consulta Pix: {e}")
        dataset = None
    progress_bar.progress(40)
            
    if dataset is not None and not dataset.empty:
        # Renomear colunas para português
        dataset.rename(columns={
            "user_id": "ID do Usuário",
            "transaction_type": "Tipo de Transação",
            "party": "Parte",
            "pix_amount": "Valor Pix",
            "pix_avg": "Ticket Médio Pix",
            "pix_count": "Quantidade de Pix",
            "percentage": "Percentual",
            "pix_amount_atypical_hours": "Valor Pix em Horário Atípico",
            "pix_count_atypical_hours": "Quantidade de Pix em Horário Atípico",
            "modelo": "Modelo"
        }, inplace=True)
            
        # Formatar as colunas numéricas para o padrão brasileiro
        colunas_formatar = ["Valor Pix", "Ticket Médio Pix", "Valor Pix em Horário Atípico"]
        for coluna in colunas_formatar:
            dataset[coluna] = dataset[coluna].apply(format_float)

        # Criar a coluna numérica para cálculos
        dataset["Valor Pix (num)"] = pd.to_numeric(
            dataset["Valor Pix"].astype(str).apply(lambda x: x.replace(".", "").replace(",", ".")), 
            errors="coerce"
        )
            
        st.markdown("""
            <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
                <h3 style='color: #1e293b; margin-bottom: 15px;'>📊 Dados Analíticos - Consulta Pix</h3>
        """, unsafe_allow_html=True)
            
        # Exibir tabela com estilo personalizado
        st.dataframe(
            dataset,
            use_container_width=True,
            hide_index=True
        )
            
        # Adicionar métricas resumidas para transações PIX
        st.markdown("""
            <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;'>
                <h3 style='color: #1e293b; margin-bottom: 15px;'>📊 Métricas Resumidas - Transações PIX</h3>
        """, unsafe_allow_html=True)
                
        # Calcular totais para o resumo sintético
        cash_in_total = dataset[dataset['Tipo de Transação'] == 'Cash In']["Valor Pix (num)"].sum()
        cash_out_total = dataset[dataset['Tipo de Transação'] == 'Cash Out']["Valor Pix (num)"].sum()
        total_atipico_pix = dataset["Valor Pix em Horário Atípico"].astype(str).apply(lambda x: x.replace(".", "").replace(",", ".")).astype(float).sum()
        total_transacoes = cash_in_total + cash_out_total
        percentual_atipico_pix = (total_atipico_pix / total_transacoes * 100) if total_transacoes > 0 else 0

        # Criar métricas resumidas para PIX
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Cash In",
                f"R$ {format_float(cash_in_total)}",
                delta=None
            )

        with col2:
            st.metric(
                "Total Cash Out",
                f"R$ {format_float(cash_out_total)}",
                delta=None
            )

        with col3:
            st.metric(
                "Total em Horários Atípicos",
                f"R$ {format_float(total_atipico_pix)}",
                delta=None
            )

        with col4:
            st.metric(
                "% Transações Atípicas",
                f"{format_percent(percentual_atipico_pix)}",
                delta=None
            )
            
        balance = cash_in_total - cash_out_total
        progress_bar.progress(60)
        
        # Carregar o CSV de apostas ("gateway_bet.csv") e cruzar com a coluna "Parte"
        try:
            csv_path = "src/gateway_bet.csv"
            df_bet = pd.read_csv(csv_path)
            st.success("Dados do gateway BET carregados com sucesso! 🎲")
        except Exception as e:
            st.error(f"Erro ao carregar o CSV 'gateway_bet.csv': {e}")
            df_bet = None
        
        if df_bet is not None and not df_bet.empty and 'gateway' in df_bet.columns:
            dataset['Parte_str'] = dataset['Parte'].astype(str).apply(lambda x: x.strip().lower())
            df_bet['gateway_str'] = df_bet['gateway'].astype(str).apply(lambda x: x.strip().lower())
            bet_mask = dataset['Parte_str'].isin(df_bet['gateway_str'])
            bet_cash_in = dataset[(dataset['Tipo de Transação'] == 'Cash In') & (bet_mask)]["Valor Pix (num)"].sum()
            bet_cash_out = dataset[(dataset['Tipo de Transação'] == 'Cash Out') & (bet_mask)]["Valor Pix (num)"].sum()
        else:
            bet_cash_in = 0
            bet_cash_out = 0
        
        prop_cash_in = (bet_cash_in / cash_in_total * 100) if cash_in_total != 0 else 0
        prop_cash_out = (bet_cash_out / cash_out_total * 100) if cash_out_total != 0 else 0
        
        summary_data = {
            "Tipo de Transação": ["Cash In", "Cash Out", "Saldo", "Bet Cash In", "Bet Cash Out"],
            "Valor Total (R$)": [cash_in_total, cash_out_total, balance, bet_cash_in, bet_cash_out],
            "Proporcional Bet": [prop_cash_in, prop_cash_out, None, None, None]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df["Valor Total (R$)"] = summary_df["Valor Total (R$)"].apply(format_brl)
        summary_df["Proporcional Bet"] = summary_df["Proporcional Bet"].apply(lambda x: format_percent(x) if pd.notnull(x) else "")
        
        progress_bar.progress(80)
        st.subheader("💡 Dados Sintéticos - Resumo")
        st.table(summary_df)
        
        # --- NOVO BLOCO: Gráfico de Barras das Maiores Transações ---
        # Selecionar as 5 maiores transações em Cash In e Cash Out com base no valor numérico
        top_cash_in = dataset[dataset['Tipo de Transação'] == 'Cash In'].nlargest(5, 'Valor Pix (num)')
        top_cash_out = dataset[dataset['Tipo de Transação'] == 'Cash Out'].nlargest(5, 'Valor Pix (num)')

        # Truncar o nome da parte para exibir apenas o texto antes do símbolo "|" e converter para maiúsculas
        top_cash_in['Parte'] = top_cash_in['Parte'].str.split('|').str[0].str.upper()
        top_cash_out['Parte'] = top_cash_out['Parte'].str.split('|').str[0].str.upper()

        # Ordenar os dados em ordem decrescente antes de criar os gráficos
        top_cash_in = top_cash_in.sort_values('Valor Pix (num)', ascending=False)
        top_cash_out = top_cash_out.sort_values('Valor Pix (num)', ascending=False)

        # Criar gráfico de barras horizontais para Cash In
        if not top_cash_in.empty:
            fig_cash_in = px.bar(
                top_cash_in,
                y='Parte',
                x='Valor Pix (num)',
                title='Top 5 Transações Cash In',
                labels={'Valor Pix (num)': 'Valor (R$)', 'Parte': ''},
                text='Valor Pix',
                color='Valor Pix (num)',
                color_continuous_scale='Greens',
                orientation='h'
            )
            fig_cash_in.update_traces(
                textposition='outside',
                texttemplate='R$ %{text}',
                hovertemplate='<b>%{y}</b><br>' +
                             'Valor: R$ %{x:,.2f}<br>' +
                             '<extra></extra>'
            )
            fig_cash_in.update_layout(
                template='plotly_white',
                xaxis_title='Valor (R$)',
                yaxis_title=None,
                showlegend=False,
                height=400,
                width=600,
                margin=dict(l=20, r=20, t=40, b=20),
                title=dict(
                    text='Top 5 Transações Cash In',
                    x=0.5,
                    y=0.95,
                    xanchor='center',
                    yanchor='top',
                    font=dict(size=20, color='#1e293b')
                ),
                yaxis=dict(
                    tickfont=dict(size=12),
                    tickangle=0,
                    categoryorder='total descending'
                ),
                xaxis=dict(
                    tickfont=dict(size=12),
                    tickformat='R$ ,.2f'
                )
            )

        # Criar gráfico de barras horizontais para Cash Out
        if not top_cash_out.empty:
            fig_cash_out = px.bar(
                top_cash_out,
                y='Parte',
                x='Valor Pix (num)',
                title='Top 5 Transações Cash Out',
                labels={'Valor Pix (num)': 'Valor (R$)', 'Parte': ''},
                text='Valor Pix',
                color='Valor Pix (num)',
                color_continuous_scale='Reds',
                orientation='h'
            )
            fig_cash_out.update_traces(
                textposition='outside',
                texttemplate='R$ %{text}',
                hovertemplate='<b>%{y}</b><br>' +
                             'Valor: R$ %{x:,.2f}<br>' +
                             '<extra></extra>'
            )
            fig_cash_out.update_layout(
                template='plotly_white',
                xaxis_title='Valor (R$)',
                yaxis_title=None,
                showlegend=False,
                height=400,
                width=600,
                margin=dict(l=20, r=20, t=40, b=20),
                title=dict(
                    text='Top 5 Transações Cash Out',
                    x=0.5,
                    y=0.95,
                    xanchor='center',
                    yanchor='top',
                    font=dict(size=20, color='#1e293b')
                ),
                yaxis=dict(
                    tickfont=dict(size=12),
                    tickangle=0,
                    categoryorder='total descending'
                ),
                xaxis=dict(
                    tickfont=dict(size=12),
                    tickformat='R$ ,.2f'
                )
            )

        # Exibir gráficos lado a lado
        if not top_cash_in.empty or not top_cash_out.empty:
            st.markdown("""
                <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;'>
                    <h3 style='color: #1e293b; margin-bottom: 15px;'>📈 Top 5 Transações</h3>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)

            if not top_cash_in.empty:
                with col1:
                    st.markdown("""
                        <div style='background-color: #f0fdf4; padding: 15px; border-radius: 8px; margin-bottom: 10px;'>
                            <h4 style='color: #166534; margin: 0;'>💵 Cash In</h4>
                        </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(fig_cash_in, use_container_width=True)

            if not top_cash_out.empty:
                with col2:
                    st.markdown("""
                        <div style='background-color: #fef2f2; padding: 15px; border-radius: 8px; margin-bottom: 10px;'>
                            <h4 style='color: #991b1b; margin: 0;'>💸 Cash Out</h4>
                        </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(fig_cash_out, use_container_width=True)
        else:
            st.warning("Nenhuma transação encontrada para exibição.")
        # --- Fim do Gráfico de Barras ---

    else:
        st.error("Nenhum dado retornado da consulta Pix. ❌")
        
    # Executar consulta de transações de cartões
    try:
        query_card_transactions = sql_manager.get_card_transactions_query(id_client)
        query_job_card = client.query(query_card_transactions)
        df_card_transactions = query_job_card.result().to_dataframe()
        st.success("Consulta Transações de Cartões concluída com sucesso! ✅")
    except Exception as e:
        st.error(f"Erro na consulta de transações de cartões: {e}")
        df_card_transactions = None
    progress_bar.progress(90)
        
    if df_card_transactions is not None and not df_card_transactions.empty:
        # Renomear colunas para português
        df_card_transactions.rename(columns={
            "card_holder_name": "Nome do Portador",
            "Total_Aprovado": "Total Aprovado",
            "Total_Aprovado_Atipico": "Total Aprovado Atípico"
        }, inplace=True)
        df_card_transactions["Total Aprovado"] = df_card_transactions["Total Aprovado"].apply(format_brl)
        df_card_transactions["Total Aprovado Atípico"] = df_card_transactions["Total Aprovado Atípico"].apply(format_brl)
        st.markdown("""
            <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;'>
                <h3 style='color: #1e293b; margin-bottom: 15px;'>📱⭕️ Transações de Cartões</h3>
        """, unsafe_allow_html=True)
        
        # Criar métricas resumidas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_aprovado = df_card_transactions['Total Aprovado'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.').astype(float).sum()
            st.metric(
                label="Total Aprovado",
                value=format_brl(total_aprovado),
                delta=None
            )
        
        with col2:
            total_atipico = df_card_transactions['Total Aprovado Atípico'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.').astype(float).sum()
            st.metric(
                label="Total Aprovado Atípico",
                value=format_brl(total_atipico),
                delta=None
            )
        
        with col3:
            percentual_atipico = (total_atipico / total_aprovado * 100) if total_aprovado > 0 else 0
            st.metric(
                label="Percentual Atípico",
                value=format_percent(percentual_atipico),
                delta=None
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Exibir tabela de transações
        st.dataframe(df_card_transactions, use_container_width=True)
    else:
        st.warning("Não há informações sobre Transações de Cartões.")
    
    # Executar consulta de informações de contato
    try:
        query_contact_info = sql_manager.get_contact_info_query(id_client)
        query_job_contact = client.query(query_contact_info)
        df_contact_info = query_job_contact.result().to_dataframe()
        st.success("Consulta de informações de contato concluída com sucesso! ✅")
    except Exception as e:
        st.error(f"Erro ao executar a consulta de informações de contato: {e}")
        df_contact_info = None
    progress_bar.progress(95)

    if df_contact_info is not None and not df_contact_info.empty:
        # Renomear colunas para português
        df_contact_info.rename(columns={
            "has_phonecast": "Possui Phonecast",
            "user_id": "ID do Usuário",
            "name": "Nome",
            "raw_phone_number": "Número de Telefone",
            "status": "Status",
            "status_reason": "Motivo do Status"
        }, inplace=True)

        # Converter has_phonecast para texto mais amigável
        df_contact_info["Possui Phonecast"] = df_contact_info["Possui Phonecast"].map({True: "Sim", False: "Não"})

        st.markdown("""
            <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;'>
                <h3 style='color: #1e293b; margin-bottom: 15px;'>📱⭕️ Informações de Contatos Bloqueados</h3>
        """, unsafe_allow_html=True)

        # Exibir tabela com estilo personalizado
        st.dataframe(
            df_contact_info,
            use_container_width=True,
            hide_index=True
        )

        # Criar tabela sintética de bloqueios por motivo
        if 'Status' in df_contact_info.columns and 'Motivo do Status' in df_contact_info.columns:
            # Filtrar apenas registros bloqueados
            df_blocked = df_contact_info[df_contact_info['Status'] != 'active'].copy()
            
            # Agrupar por motivo do status e contar
            blocked_summary = df_blocked.groupby('Motivo do Status').size().reset_index(name='Quantidade')
            
            # Ordenar por quantidade em ordem decrescente
            blocked_summary = blocked_summary.sort_values('Quantidade', ascending=False)
            
            # Calcular o total
            total_blocked = blocked_summary['Quantidade'].sum()
            
            # Adicionar coluna de percentual
            blocked_summary['Percentual'] = (blocked_summary['Quantidade'] / total_blocked * 100).round(2)
            
            # Formatar percentual
            blocked_summary['Percentual'] = blocked_summary['Percentual'].apply(lambda x: f"{x:.2f}%")
            
            st.markdown("""
                <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;'>
                    <h3 style='color: #1e293b; margin-bottom: 15px;'>🚫 Análise de Bloqueios por Motivo</h3>
            """, unsafe_allow_html=True)
            
            # Exibir métrica do total de bloqueios
            st.metric(
                "Total de Registros Bloqueados",
                f"{total_blocked}",
                delta=None
            )
            
            # Exibir tabela sintética
            st.dataframe(
                blocked_summary,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("Nenhuma informação de contato encontrada para este cliente.")
    
    # Executar consulta de transações PEP se o filtro estiver ativado
    if st.session_state.show_pep:
        try:
            query_pep = sql_manager.get_pep_query(id_client)
            
            query_job_pep = client.query(query_pep)
            df_pep = query_job_pep.result().to_dataframe()
            
            if not df_pep.empty:
                # Renomear colunas para português
                df_pep.rename(columns={
                    "flagged_user_id": "ID do Usuário",
                    "transfer_type": "Tipo de Transferência",
                    "total_amount": "Valor Total",
                    "pep_document_number": "CPF PEP",
                    "name": "Nome PEP",
                    "agency": "Órgão",
                    "job": "Cargo",
                    "job_description": "Descrição do Cargo",
                    "started_at": "Data de Início",
                    "final_eligibility_date": "Data Final de Elegibilidade"
                }, inplace=True)
                
                # Formatar valores monetários
                df_pep["Valor Total"] = df_pep["Valor Total"].apply(lambda x: f"R$ {x:,.2f}")
                
                # Formatar datas
                df_pep["Data de Início"] = pd.to_datetime(df_pep["Data de Início"]).dt.strftime("%d/%m/%Y")
                df_pep["Data Final de Elegibilidade"] = pd.to_datetime(df_pep["Data Final de Elegibilidade"]).dt.strftime("%d/%m/%Y")
                
                # Converter tipos de transferência para português
                df_pep["Tipo de Transferência"] = df_pep["Tipo de Transferência"].map({
                    "cash-in": "Entrada",
                    "cash-out": "Saída"
                })
                
                st.markdown("""
                    <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;'>
                        <h3 style='color: #1e293b; margin-bottom: 15px;'>👥 Transações com PEP</h3>
                """, unsafe_allow_html=True)
                
                # Exibir tabela com estilo personalizado
                st.dataframe(
                    df_pep,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Exibir métricas
                total_pep = len(df_pep)
                total_value = df_pep["Valor Total"].str.replace("R$ ", "").str.replace(",", "").astype(float).sum()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Total de Transações com PEP",
                        f"{total_pep}",
                        delta=None
                    )
                with col2:
                    st.metric(
                        "Valor Total das Transações",
                        f"R$ {total_value:,.2f}",
                        delta=None
                    )
            else:
                st.info("Nenhuma transação com PEP encontrada para este cliente.")
                
        except Exception as e:
            st.error(f"Erro ao executar a consulta de transações PEP: {e}")
    
    # Executar consulta de cartões corporativos se o filtro estiver ativado
    if st.session_state.show_corporate_cards:
        try:
            query_corporate_cards = sql_manager.get_corporate_cards_query(id_client)
            
            query_job_corporate = client.query(query_corporate_cards)
            df_corporate = query_job_corporate.result().to_dataframe()
            
            if not df_corporate.empty:
                # Renomear colunas para português
                df_corporate.rename(columns={
                    "card_number": "Número do Cartão",
                    "card_holder_name": "Nome do Portador",
                    "sum_30_days": "Valor 30 Dias",
                    "sum_60_days": "Valor 60 Dias",
                    "sum_90_days": "Valor 90 Dias",
                    "total_sum": "Valor Total",
                    "night_sum": "Valor em Horário Noturno"
                }, inplace=True)
                
                # Formatar valores monetários
                colunas_monetarias = ["Valor 30 Dias", "Valor 60 Dias", "Valor 90 Dias", "Valor Total", "Valor em Horário Noturno"]
                for coluna in colunas_monetarias:
                    df_corporate[coluna] = df_corporate[coluna].apply(lambda x: f"R$ {x:,.2f}")
                
                st.markdown("""
                    <div style='background-color: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;'>
                        <h3 style='color: #1e293b; margin-bottom: 15px;'>💳 Cartões Corporativos</h3>
                """, unsafe_allow_html=True)
                
                # Exibir tabela com estilo personalizado
                st.dataframe(
                    df_corporate,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Exibir métricas
                total_cards = len(df_corporate)
                
                # Converter valores monetários para cálculos
                df_corporate["Valor Total (num)"] = df_corporate["Valor Total"].str.replace("R$ ", "").str.replace(",", "").astype(float)
                df_corporate["Valor Noturno (num)"] = df_corporate["Valor em Horário Noturno"].str.replace("R$ ", "").str.replace(",", "").astype(float)
                
                total_value = df_corporate["Valor Total (num)"].sum()
                total_night = df_corporate["Valor Noturno (num)"].sum()
                percent_night = (total_night / total_value * 100) if total_value > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Total de Cartões Corporativos",
                        f"{total_cards}",
                        delta=None
                    )
                with col2:
                    st.metric(
                        "Valor Total das Transações",
                        f"R$ {total_value:,.2f}",
                        delta=None
                    )
                with col3:
                    st.metric(
                        "Valor em Horário Noturno",
                        f"R$ {total_night:,.2f}",
                        delta=f"{percent_night:.2f}% do total"
                    )
            else:
                st.info("Nenhuma transação com cartões corporativos encontrada para este cliente.")
                
        except Exception as e:
            st.error(f"Erro ao executar a consulta de cartões corporativos: {e}")
    
    # Marcar a análise como concluída
    st.session_state.analysis_done = True
    st.session_state.should_analyze = False
    progress_bar.progress(100)
    
    st.markdown("""
        <div style='background-color: #ecfdf5; padding: 20px; border-radius: 12px; margin: 20px 0;'>
            <h3 style='color: #059669; margin-bottom: 10px;'>✅ Análise Concluída!</h3>
            <p style='color: #065f46; line-height: 1.6;'>
                A análise foi realizada com sucesso. Você pode visualizar todos os dados e gráficos acima.
                Para realizar uma nova análise, basta inserir um novo ID de cliente.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Limpar dados da sessão após conclusão
    clean_session_state()
    
    # Forçar coleta de lixo
    import gc
    gc.collect()