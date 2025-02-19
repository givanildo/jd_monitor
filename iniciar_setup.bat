@echo off
echo Removendo arquivos antigos...
mpremote rm :main.py
mpremote rm :web_server.py
mpremote rm :j1939_parser.py

echo Copiando novos arquivos...
mpremote cp main.py :main.py
mpremote cp web_server.py :web_server.py
mpremote cp j1939_parser.py :j1939_parser.py

echo Reiniciando ESP32...
mpremote reset

echo Iniciando console...
mpremote repl 