import yfinance as yf
import pandas as pd
import json
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
import warnings

# Suprime avisos não críticos
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- 1. CONFIGURAÇÃO E INICIALIZAÇÃO ---
load_dotenv()
DATA_DIR = 'data'
LOG_DIR = 'logs'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

log_filename = os.path.join(LOG_DIR, f"analise_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler()]
)

EMPRESAS = {
    "PETR4.SA": "Petrobras",
    "RRRP3.SA": "3R Petroleum",
    "RECV3.SA": "PetroRecôncavo",
    "ENAT3.SA": "Enauta"
}
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
JSON_SUMMARY_FILE = os.path.join(DATA_DIR, 'resumo_analise_diaria.json')
XML_SUMMARY_FILE = os.path.join(DATA_DIR, 'resumo_analise_diaria.xml')


class AnalisadorEmpresa:
    def __init__(self, ticker, nome):
        self.ticker = ticker
        self.nome = nome
        self.historico_csv_path = os.path.join(DATA_DIR, f"{self.ticker}_historico.csv")
        self.historico_excel_path = os.path.join(DATA_DIR, f"{self.ticker}_historico.xlsx")
        self.df_historico = None
        self.dados_consolidados = {}

    def gerenciar_historico(self):
        """
        Gerencia o histórico de cotações, sempre garantindo que CSV e Excel estejam salvos.
        """
        try:
            df_local = pd.read_csv(self.historico_csv_path) if os.path.exists(self.historico_csv_path) else None
            df_final = None

            if df_local is not None and not df_local.empty:
                df_local['Date'] = pd.to_datetime(df_local['Date'])
                ultima_data = df_local['Date'].max().date()
                if ultima_data < datetime.now().date():
                    data_inicio_busca = (ultima_data + timedelta(days=1)).strftime('%Y-%m-%d')
                    logging.info(f"Buscando dados para {self.ticker} a partir de {data_inicio_busca}...")
                    stock = yf.Ticker(self.ticker)
                    df_novo = stock.history(start=data_inicio_busca)
                    if not df_novo.empty:
                        df_novo.reset_index(inplace=True)
                        df_novo['Date'] = pd.to_datetime(df_novo['Date'].dt.date)
                        df_final = pd.concat([df_local, df_novo]).drop_duplicates(subset=['Date'], keep='last').sort_values(by='Date')
                    else:
                        logging.info(f"Nenhum dado novo encontrado para {self.ticker}.")
                        df_final = df_local
                else:
                    logging.info(f"Histórico de {self.ticker} já está atualizado.")
                    df_final = df_local
            else:
                logging.info(f"Nenhum histórico local para {self.ticker}. Baixando dados completos...")
                stock = yf.Ticker(self.ticker)
                df_final = stock.history(period="max")
                if df_final.empty:
                    logging.warning(f"Nenhum dado histórico encontrado para {self.ticker} na API.")
                    return False
                df_final.reset_index(inplace=True)
                df_final['Date'] = pd.to_datetime(df_final['Date'].dt.date)

            # --- CORREÇÃO: SALVA O DATAFRAME FINAL EM AMBOS OS FORMATOS, SEMPRE ---
            if df_final is not None and not df_final.empty:
                df_final.to_csv(self.historico_csv_path, index=False)
                df_final.to_excel(self.historico_excel_path, index=False, engine='openpyxl')
                self.df_historico = df_final
                logging.info(f"Histórico de {self.ticker} salvo em CSV e Excel.")
                return True
            else:
                logging.warning(f"Não foi possível obter ou carregar dados para {self.ticker}.")
                return False

        except Exception as e:
            logging.error(f"Falha crítica ao gerenciar histórico de {self.ticker}: {e}")
            return False

    def analisar_sentimento_com_newsapi(self):
        """ Analisa o sentimento das notícias usando a NewsAPI. """
        if not NEWS_API_KEY or NEWS_API_KEY == "SUA_CHAVE_API_AQUI":
            logging.error("Chave da NewsAPI não configurada. Pulando análise de sentimento.")
            return 0.0
        try:
            logging.info(f"Analisando sentimento para {self.nome} via NewsAPI...")
            url = f"https://newsapi.org/v2/everything?q={self.nome}&language=pt&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            artigos = response.json().get("articles", [])
            if not artigos:
                logging.warning(f"Nenhum artigo encontrado para {self.nome} na NewsAPI.")
                return 0.0
            manchetes = [artigo['title'] for artigo in artigos[:20] if artigo.get('title')]
            analyzer = SentimentIntensityAnalyzer()
            scores = [analyzer.polarity_scores(text)['compound'] for text in manchetes]
            sentimento_medio = np.mean(scores) if scores else 0.0
            logging.info(f"Sentimento médio para {self.nome}: {sentimento_medio:.4f}")
            return sentimento_medio
        except Exception as e:
            logging.error(f"Erro ao analisar sentimento para {self.nome}: {e}")
            return 0.0

    def _criar_features_para_ia(self, df):
        """ Cria indicadores técnicos (features) para o modelo de IA. """
        df_feat = df.copy()
        df_feat['SMA_7'] = df_feat['Close'].rolling(window=7).mean()
        df_feat['SMA_14'] = df_feat['Close'].rolling(window=14).mean()
        delta = df_feat['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_feat['RSI'] = 100 - (100 / (1 + rs))
        df_feat.dropna(inplace=True)
        return df_feat

    def fazer_previsao_com_ia(self, sentimento_atual):
        """ Faz a predição de preços usando um modelo de IA (Random Forest). """
        if self.df_historico is None or self.df_historico.empty: return None
        try:
            df_com_features = self._criar_features_para_ia(self.df_historico)
            if len(df_com_features) < 50:
                logging.warning(f"Não há dados suficientes para treinar IA para {self.ticker}.")
                return None
            logging.info(f"Treinando modelo de IA para {self.ticker}...")
            df_com_features['Target'] = df_com_features['Close'].shift(-1)
            df_com_features.dropna(inplace=True)
            features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_7', 'SMA_14', 'RSI']
            X = df_com_features[features]
            y = df_com_features['Target']
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X, y)
            ultimo_dia = X.iloc[-1].values.reshape(1, -1)
            previsao_dia_seguinte = model.predict(ultimo_dia)[0]
            ultimo_preco = df_com_features['Close'].iloc[-1]
            tendencia_semanal = (previsao_dia_seguinte - ultimo_preco) * 7
            previsoes = {
                "proximo_dia": round(previsao_dia_seguinte, 2),
                "proxima_semana": round(ultimo_preco + tendencia_semanal, 2)
            }
            return previsoes
        except Exception as e:
            logging.error(f"Erro ao gerar previsões com IA para {self.ticker}: {e}")
            return None

    def consolidar_dados(self, sentimento, previsoes):
        """ Consolida os dados da análise em um dicionário. """
        if self.df_historico is None or previsoes is None: return
        ultima = self.df_historico.iloc[-1]
        self.dados_consolidados = {
            "nome_empresa": self.nome, "data_analise": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "ultima_cotacao": {"data": pd.to_datetime(ultima["Date"]).strftime('%Y-%m-%d'), "abertura": round(ultima["Open"], 2), "alta": round(ultima["High"], 2), "baixa": round(ultima["Low"], 2), "fechamento": round(ultima["Close"], 2), "volume": int(ultima["Volume"])},
            "sentimento_noticias": round(sentimento, 4), "previsoes_ia": previsoes
        }
        logging.info(f"Dados para {self.ticker} consolidados.")

def salvar_resumo_final(dados, arquivo_json, arquivo_xml):
    """ Salva o resumo da análise do dia em JSON e XML. """
    try:
        logging.info(f"Salvando resumo da análise em {arquivo_json}...")
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e: logging.error(f"Falha ao salvar resumo JSON: {e}")
    try:
        logging.info(f"Salvando resumo da análise em {arquivo_xml}...")
        root = ET.Element("AnaliseAcoes")
        for ticker, info in dados.items():
            empresa_elem = ET.SubElement(root, "Empresa", ticker=ticker)
            ET.SubElement(empresa_elem, "Nome").text = info.get("nome_empresa")
            ET.SubElement(empresa_elem, "DataAnalise").text = info.get("data_analise")
            cot_elem = ET.SubElement(empresa_elem, "UltimaCotacao")
            for k, v in info.get("ultima_cotacao", {}).items(): ET.SubElement(cot_elem, k.capitalize()).text = str(v)
            ET.SubElement(empresa_elem, "SentimentoNoticias").text = str(info.get("sentimento_noticias"))
            prev_elem = ET.SubElement(empresa_elem, "PrevisoesIA")
            for k, v in info.get("previsoes_ia", {}).items(): ET.SubElement(prev_elem, k.replace("_", " ")).text = str(v)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(arquivo_xml, encoding='utf-8', xml_declaration=True)
    except Exception as e: logging.error(f"Falha ao salvar resumo XML: {e}")

def main():
    """ Orquestra todo o processo de análise. """
    logging.info("--- INICIANDO ROTINA DE ANÁLISE DE AÇÕES COM IA ---")
    dados_resumo_diario = {}
    for ticker, nome in EMPRESAS.items():
        logging.info(f"--- Processando {nome} ({ticker}) ---")
        analisador = AnalisadorEmpresa(ticker, nome)
        if not analisador.gerenciar_historico():
            logging.warning(f"Não foi possível obter dados para {ticker}. Pulando.")
            continue
        sentimento = analisador.analisar_sentimento_com_newsapi()
        previsoes = analisador.fazer_previsao_com_ia(sentimento)
        analisador.consolidar_dados(sentimento, previsoes)
        if analisador.dados_consolidados:
            dados_resumo_diario[ticker] = analisador.dados_consolidados
    if dados_resumo_diario:
        salvar_resumo_final(dados_resumo_diario, JSON_SUMMARY_FILE, XML_SUMMARY_FILE)
        logging.info("Análise com IA concluída. Resumos salvos com sucesso.")
    else:
        logging.warning("Nenhuma empresa foi processada com sucesso.")
    logging.info("--- ROTINA DE ANÁLISE FINALIZADA ---")

if __name__ == "__main__":
    main()
