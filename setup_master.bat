@echo off
cls
color 0A

echo ========================================================
echo    Monitor CAN Bus - John Deere - Assistente de Setup
echo ========================================================
echo.

:: Verifica se está rodando como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Por favor, execute este script como Administrador!
    echo Clique com botao direito e selecione "Executar como administrador"
    pause
    exit
)

:: Verifica se o Git está instalado
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Git nao encontrado! Por favor, instale o Git primeiro.
    echo Download: https://git-scm.com/download/win
    pause
    exit
)

echo Configurando ambiente...
echo.

:: Cria estrutura de diretórios
echo Criando estrutura de diretorios...
if exist john-deere-canbus-monitor (
    echo Pasta do projeto ja existe. Deseja recriar? (S/N)
    set /p recria=
    if /i "%recria%"=="S" (
        rmdir /s /q john-deere-canbus-monitor
    ) else (
        echo Operacao cancelada.
        pause
        exit
    )
)

mkdir john-deere-canbus-monitor
cd john-deere-canbus-monitor
mkdir src\esp32
mkdir src\dashboard
mkdir docs\images
mkdir tests

:: Copia arquivos
echo.
echo Copiando arquivos do projeto...
copy ..\main.py src\esp32\ >nul
copy ..\web_server.py src\esp32\ >nul
copy ..\j1939_parser.py src\esp32\ >nul
copy ..\dashboard.py src\dashboard\ >nul
copy ..\README.md . >nul

:: Cria requirements.txt
echo.
echo Criando requirements.txt...
(
echo streamlit
echo pandas
echo plotly
echo folium
echo streamlit-folium
echo requests
echo mpremote
echo esptool
) > requirements.txt

:: Cria .gitignore mais completo
echo.
echo Criando .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo .env
echo .venv
echo env/
echo venv/
echo ENV/
echo *.log
echo # IDEs
echo .idea/
echo .vscode/
echo *.swp
echo *.swo
echo # Sistema
echo .DS_Store
echo Thumbs.db
) > .gitignore

:: Configuração do Git
echo.
echo Configurando Git...
git init
git add .
git commit -m "Primeiro commit: Monitor CAN Bus para Tratores John Deere"
git branch -M main

:: Solicita informações do GitHub
echo.
echo ========================================================
echo                Configuracao do GitHub
echo ========================================================
echo.
set /p github_user=Digite seu usuario do GitHub: 
set /p repo_name=Digite o nome do repositorio [john-deere-canbus-monitor]: 
if "%repo_name%"=="" set repo_name=john-deere-canbus-monitor

:: Tenta configurar o remote e fazer push
echo.
echo Configurando repositorio remoto...
git remote add origin https://github.com/%github_user%/%repo_name%.git

echo.
echo Tentando fazer push para o GitHub...
git push -u origin main

if %errorLevel% neq 0 (
    echo.
    echo ATENCAO: Nao foi possivel fazer o push automaticamente.
    echo 1. Crie um novo repositorio em: https://github.com/new
    echo 2. Nome do repositorio: %repo_name%
    echo 3. Nao inicialize com README
    echo 4. Depois execute:
    echo    git remote add origin https://github.com/%github_user%/%repo_name%.git
    echo    git push -u origin main
)

:: Cria script de atualização
echo.
echo Criando script de atualizacao...
(
echo @echo off
echo color 0A
echo echo Atualizando repositorio...
echo.
echo git add .
echo set /p msg=Digite a mensagem do commit: 
echo git commit -m "%%msg%%"
echo git push
echo.
echo echo Repositorio atualizado!
echo pause
) > update.bat

echo.
echo ========================================================
echo                   Setup Concluido!
echo ========================================================
echo.
echo Scripts criados:
echo - update.bat : Use para atualizar o repositorio
echo.
echo Estrutura do projeto criada em:
echo %CD%
echo.
echo Para instalar as dependencias, execute:
echo pip install -r requirements.txt
echo.
echo Para iniciar o dashboard:
echo cd src/dashboard
echo streamlit run dashboard.py
echo.
pause 