@echo off
cls
color 0A

echo ========================================================
echo    Setup Final GitHub - Monitor CAN Bus
echo ========================================================
echo.

:: Verifica se está na pasta correta
if not exist "john-deere-canbus-monitor" (
    echo Pasta do projeto nao encontrada!
    echo Criando estrutura inicial...
    
    :: Executa setup inicial
    call setup_simples.bat
)

:: Entra na pasta do projeto
cd john-deere-canbus-monitor

:: Configura Git global com seu email
echo.
echo Configurando credenciais globais...
git config --global user.name "givanildo"
git config --global user.email "givanildobrunetta@gmail.com"

:: Solicita apenas o token
echo.
echo Para gerar um novo token:
echo 1. Acesse: https://github.com/settings/tokens
echo 2. Clique em "Generate new token (classic)"
echo 3. De um nome como "CAN Bus Monitor"
echo 4. Marque a opcao "repo"
echo 5. Copie o token gerado
echo.
set /p github_token=Cole seu token do GitHub: 

:: Limpa configurações antigas
echo.
echo Limpando configuracoes antigas...
git remote remove origin
git reset --hard HEAD

:: Força reconfiguração do repositório
echo.
echo Reconfigurando repositorio...
git add .
git commit -m "Configuracao inicial: Monitor CAN Bus para Tratores John Deere"
git branch -M main

:: Adiciona novo remote com token
echo.
echo Configurando remote com seu token...
git remote add origin https://givanildo:%github_token%@github.com/givanildo/john-deere-canbus-monitor.git

:: Força o push
echo.
echo Enviando para o GitHub...
git push -f -u origin main

if errorlevel 1 (
    echo.
    echo ATENCAO: Erro ao fazer push!
    echo Tentando solucao alternativa...
    
    git pull origin main --allow-unrelated-histories
    git add .
    git commit -m "Merge: Resolucao de conflitos"
    git push -u origin main
    
    if errorlevel 1 (
        echo.
        echo ATENCAO: Ainda nao foi possivel fazer o push!
        echo 1. Verifique se criou o repositorio em:
        echo    https://github.com/givanildo/john-deere-canbus-monitor
        echo 2. Verifique se o token esta correto
        echo 3. Execute este script novamente
    )
) else (
    echo.
    echo ========================================================
    echo          Repositorio configurado com sucesso!
    echo ========================================================
    echo.
    echo Seu codigo esta disponivel em:
    echo https://github.com/givanildo/john-deere-canbus-monitor
    
    echo.
    echo Proximo passo:
    echo 1. Instale as dependencias: pip install -r requirements.txt
    echo 2. Execute o dashboard: streamlit run src/dashboard/dashboard.py
)

echo.
pause 