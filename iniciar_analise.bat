@echo off
TITLE Dashboard de Analise de Acoes

ECHO ==========================================================
ECHO  INICIANDO ROTINA DE ANALISE E DASHBOARD DE ACOES
ECHO ==========================================================
ECHO.

REM --- Passo 1: Ativar o ambiente virtual ---
ECHO [1/3] Ativando o ambiente virtual Python...
CALL .venv\Scripts\activate
IF %errorlevel% neq 0 (
ECHO ERRO: Nao foi possivel ativar o ambiente virtual.
ECHO Verifique se a pasta '.venv' existe neste diretorio.
PAUSE
EXIT /B
)
ECHO Ambiente virtual ativado com sucesso!
ECHO.

REM --- Passo 2: Executar o script de analise de dados ---
REM !!! ATENCAO: Verifique se o nome do arquivo Python abaixo esta correto !!!
ECHO [2/3] Executando o script de analise com IA para atualizar os dados...
python analise_acoes_petroleo-006.py
ECHO.
ECHO Analise de dados concluida!
ECHO.

REM --- Passo 3: Iniciar o dashboard interativo ---
REM !!! ATENCAO: Verifique se o nome do arquivo do dashboard abaixo esta correto !!!
ECHO [3/3] Abrindo o dashboard interativo no seu navegador...
streamlit run dashboard_analise.py

ECHO.
ECHO ==========================================================
ECHO  O dashboard esta rodando. Feche esta janela para encerrar.
ECHO ==========================================================
PAUSE