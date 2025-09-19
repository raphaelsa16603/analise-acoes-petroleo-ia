import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Análise de Ações",
    page_icon="📊",
    layout="wide"
)

# --- FUNÇÕES AUXILIARES ---

def carregar_dados_resumo():
    """Carrega o arquivo JSON com o resumo da análise diária."""
    arquivo_resumo = os.path.join('data', 'resumo_analise_diaria.json')
    if os.path.exists(arquivo_resumo):
        with open(arquivo_resumo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def carregar_dados_historicos(ticker):
    """Carrega o arquivo Excel com o histórico de cotações."""
    arquivo_historico = os.path.join('data', f"{ticker}_historico.xlsx")
    if os.path.exists(arquivo_historico):
        df = pd.read_excel(arquivo_historico)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return None

def calcular_indicadores(df):
    """Calcula médias móveis e Bandas de Bollinger para o gráfico."""
    df['SMA_21'] = df['Close'].rolling(window=21).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # Bandas de Bollinger
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['Banda Superior'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['Banda Inferior'] = df['SMA_20'] - (df['STD_20'] * 2)
    
    return df

# --- TÍTULO E CABEÇALHO ---

st.title("📊 Dashboard de Análise de Ações de Petróleo & Gás")
st.markdown(f"**Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- CARREGAMENTO DOS DADOS ---

dados_resumo = carregar_dados_resumo()

if not dados_resumo:
    st.error("Arquivo 'resumo_analise_diaria.json' não encontrado! Execute o script de análise primeiro.")
    st.stop()

# --- BARRA LATERAL (SELEÇÃO DA EMPRESA) ---

st.sidebar.header("Selecione a Empresa")
lista_empresas = [info['nome_empresa'] for info in dados_resumo.values()]
nome_empresa_selecionada = st.sidebar.selectbox("Empresa", lista_empresas)

# Encontra o ticker correspondente ao nome da empresa selecionada
ticker_selecionado = None
for ticker, info in dados_resumo.items():
    if info['nome_empresa'] == nome_empresa_selecionada:
        ticker_selecionado = ticker
        break

if not ticker_selecionado:
    st.error("Não foi possível encontrar o ticker para a empresa selecionada.")
    st.stop()

# --- EXIBIÇÃO DOS DADOS DA EMPRESA SELECIONADA ---

st.header(f"Análise de: {nome_empresa_selecionada} ({ticker_selecionado})")

dados_empresa = dados_resumo[ticker_selecionado]

# Métricas Principais em colunas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=f"Último Fechamento ({dados_empresa['ultima_cotacao']['data']})",
        value=f"R$ {dados_empresa['ultima_cotacao']['fechamento']:.2f}"
    )

with col2:
    sentimento = dados_empresa['sentimento_noticias']
    emoji_sentimento = "😐 Neutro"
    if sentimento > 0.15:
        emoji_sentimento = "😊 Positivo"
    elif sentimento < -0.15:
        emoji_sentimento = "😞 Negativo"
    
    st.metric(
        label="Sentimento das Notícias",
        value=emoji_sentimento,
        help=f"Score calculado: {sentimento:.4f}"
    )

with col3:
    st.metric(
        label="Previsão IA (Próximo Dia)",
        value=f"R$ {dados_empresa['previsoes_ia']['proximo_dia']:.2f}",
        delta=f"{dados_empresa['previsoes_ia']['proximo_dia'] - dados_empresa['ultima_cotacao']['fechamento']:.2f}"
    )

with col4:
    st.metric(
        label="Previsão IA (Próxima Semana)",
        value=f"R$ {dados_empresa['previsoes_ia']['proxima_semana']:.2f}",
        delta=f"{dados_empresa['previsoes_ia']['proxima_semana'] - dados_empresa['ultima_cotacao']['fechamento']:.2f}"
    )

st.markdown("---")

# --- GRÁFICO HISTÓRICO ---

st.subheader("Histórico de Cotações com Indicadores")

df_historico = carregar_dados_historicos(ticker_selecionado)

if df_historico is not None:
    df_grafico = calcular_indicadores(df_historico.tail(365)) # Pega o último ano para o gráfico
    
    st.line_chart(
        df_grafico,
        x='Date',
        y=['Close', 'Banda Superior', 'Banda Inferior', 'SMA_50'],
        color=['#0072B2', '#D55E00', '#D55E00', '#009E73'] # Cores personalizadas
    )
    st.caption("Gráfico mostrando o preço de fechamento (azul), Bandas de Bollinger (laranja) e Média Móvel de 50 dias (verde).")

else:
    st.warning(f"Arquivo de histórico para {ticker_selecionado} não foi encontrado.")

# --- EXIBIÇÃO DOS DADOS BRUTOS (OPCIONAL) ---
with st.expander("Ver dados da última análise"):
    st.json(dados_empresa)
