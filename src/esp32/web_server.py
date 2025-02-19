# Instala bibliotecas
mpremote mip install microdot
mpremote mip install urequests

# Copia arquivos
mpremote cp src/esp32/main.py :main.py
mpremote cp src/esp32/index.html :index.html

# Reinicia
mpremote reset