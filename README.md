# 📊 Análise de Ações de Petróleo & Gás com IA

Este projeto realiza **análise preditiva** e **análise de sentimento de notícias** para empresas de Petróleo & Gás listadas na B3, utilizando:
- [yfinance](https://pypi.org/project/yfinance/) para dados históricos de ações,
- [NewsAPI](https://newsapi.org/) para análise de sentimento de notícias,
- **IA com Random Forest** para previsão de preços,
- **Streamlit** para visualização interativa em dashboard.

---

## 📂 Estrutura do Projeto
```
├── analise_acoes_petroleo.py   # Script principal de análise
├── dashboard_analise.py            # Dashboard interativo (Streamlit)
├── iniciar_analise.bat             # Script Windows para iniciar análise
├── requirements.txt                # Dependências do projeto
├── data/                           # Arquivos de dados gerados (JSON, XML, históricos)
├── logs/                           # Logs de execução
└── .env                            # Configurações sensíveis (não versionado)
```

---

## ⚙️ Configuração do Ambiente

### 1️⃣ Criar ambiente virtual (opcional, mas recomendado)
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 2️⃣ Instalar dependências
```bash
pip install -r requirements.txt
```

### 3️⃣ Obter chave da NewsAPI
- Crie uma conta gratuita em [https://newsapi.org](https://newsapi.org).
- Após login, copie sua chave de API.

### 4️⃣ Criar arquivo `.env`
Na raiz do projeto, crie um arquivo chamado **`.env`** com o seguinte conteúdo:

```env
NEWS_API_KEY="SUA_CHAVE_AQUI"
```

⚠️ **Importante:**  
O arquivo `.env` **não deve ser versionado** no GitHub. O repositório já deve conter um `.gitignore` para garantir isso.

---

## ▶️ Execução

### Rodar a análise das ações
```bash
python analise_acoes_petroleo.py
```

Isso irá gerar:
- `data/resumo_analise_diaria.json`
- `data/resumo_analise_diaria.xml`
- Históricos em CSV/Excel para cada empresa.

### Rodar o dashboard interativo
```bash
streamlit run dashboard_analise.py
```

O Streamlit abrirá no navegador em:  
👉 [http://localhost:8501](http://localhost:8501)

---

## 📊 Exemplo de Output
- Análise de sentimentos das notícias (positivo, neutro, negativo).
- Previsão de preço do próximo dia e da próxima semana.
- Dashboard interativo com gráficos de preços, médias móveis e Bandas de Bollinger.

---

## 📜 Licença
Este projeto é distribuído sob a licença **MIT**.
