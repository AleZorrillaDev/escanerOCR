@echo off
echo Iniciando Servidor...
echo Asegurate de haber instalado Tesseract OCR!
python -m pip install -r requirements.txt
python main.py
pause
