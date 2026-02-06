import os
import re
import socket
import logging
import io
import base64
from typing import List, Dict

import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from flask_sock import Sock
from simple_websocket.ws import Server as WebSocketServer

import qrcode
from PIL import Image, ImageOps
import pytesseract

# --- Configuración de Logs ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuración Flask Application ---
app = Flask(__name__, static_folder='static', template_folder='templates')
sock = Sock(app)

# --- Configuración Tesseract ---
tesseract_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\alets\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
]

tesseract_cmd = None
for path in tesseract_paths:
    if os.path.exists(path):
        tesseract_cmd = path
        break

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    logger.info(f"Tesseract encontrado en: {tesseract_cmd}")
else:
    logger.warning("Tesseract NO encontrado. El OCR fallará.")

# --- Funciones Auxiliares ---
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def clean_ocr_number(text: str) -> str:
    """
    Corrige errores comunes de OCR en números (ej: 'O'->'0', 'l'->'1').
    """
    replacements = {
        'O': '0', 'o': '0', 'Q': '0', 'D': '0', 'C': '0',
        'I': '1', 'l': '1', '|': '1', '!': '1', 'i': '1', 'L': '1',
        'Z': '2', 'E': '3', 'A': '4', 'S': '5', '$': '5',
        'G': '6', 'T': '7', 'B': '8', 'g': '9'
    }
    cleaned = text
    for char, digit in replacements.items():
        cleaned = cleaned.replace(char, digit)
    return re.sub(r'\D', '', cleaned)

def validate_ruc(ruc: str) -> bool:
    """Valida RUC peruano usando algoritmo Modulo 11"""
    if len(ruc) != 11 or not ruc.isdigit():
        return False
    factors = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = 0
    try:
        for i in range(10):
            suma += int(ruc[i]) * factors[i]
    except ValueError:
        return False
    residuo = suma % 11
    complemento = 11 - residuo
    digito = 0 if complemento == 10 else (1 if complemento == 11 else complemento)
    return digito == int(ruc[10])

def preprocess_image(pil_image):
    """
    Preprocesamiento "Sweet Spot" (Solo Adaptive Threshold).
    Sin redimensionado ni erosion agresiva.
    """
    open_cv_image = np.array(pil_image) 
    
    if len(open_cv_image.shape) == 2:
         img_gray = open_cv_image
    else:
         img_gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)

    # Median Blur suave
    img_blur = cv2.medianBlur(img_gray, 3)

    # Adaptive Threshold: Configuración clasica para documentos
    img_thresh = cv2.adaptiveThreshold(
        img_blur, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        31, # Block size 
        15  # Constant
    )
    # Sin erosion/dilatacion ni resizing
    return Image.fromarray(img_thresh)

def to_base64_img(pil_img):
    buffered = io.BytesIO()
    pil_img.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode()

def extract_data_from_text(text: str) -> Dict[str, str]:
    data = {}
    
    text_clean = re.sub(r'  +', ' ', text)

    # 1. EXPEDIENTE SIGAD (Se mantiene lógica mejorada)
    exp_sigad_match = re.search(r'\b(\d{3}-[A-Z0-9]+-\d{4}-\d+-\d)\b', text)
    if exp_sigad_match:
        data["exp_sigad"] = exp_sigad_match.group(1)

    # 2. RESOLUCIÓN COACTIVA
    # Intento 1: Regex explicito
    res_match = re.search(r'(?i)(?:RESOLUCI[ÓO]N|RES\.?)\s*(?:COACTIVA)?\s*(?:N[º°])?\s*([\dOIZSB]+)', text)
    if res_match:
        raw = clean_ocr_number(res_match.group(1))
        if len(raw) >= 10: data["res_coactiva"] = raw
    else:
        # Intento 2: Buscar numero largo 133...
        possibles = re.findall(r'\b(133\d{10})\b', clean_ocr_number(text))
        if possibles: data["res_coactiva"] = possibles[0]

    # 3. EXPEDIENTE RC
    exp_rc_match = re.search(r'(?i)EXPEDIENTE\s+(?:N[ÚU]MERO|N[º°])\s*[:\.]?\s*([\dOIZSB]+)', text)
    if exp_rc_match:
        data["expediente_rc"] = clean_ocr_number(exp_rc_match.group(1))

    # 4. RUCs (Lógica robusta)
    all_numbers = re.findall(r'\b\d{11}\b', clean_ocr_number(text))
    valid_rucs = []
    seen = set()
    for num in all_numbers:
        if validate_ruc(num) and num not in seen:
            valid_rucs.append(num)
            seen.add(num)
    
    if valid_rucs:
        data["ruc_contribuyente"] = valid_rucs[0]
        if len(valid_rucs) > 1:
            data["ruc_tercero"] = valid_rucs[-1]

    # 5. NOMBRE CONTRIBUYENTE
    lines = text_clean.split('\n')
    for i, line in enumerate(lines):
        if "DEUDOR" in line.upper() or "CONTRIBUYENTE" in line.upper():
             match = re.search(r'[:\.]\s*(.*)', line)
             if match:
                 val = match.group(1).strip()
                 if len(val) > 4: data["nombre_contribuyente"] = val
             elif i + 1 < len(lines):
                 data["nombre_contribuyente"] = lines[i+1].strip()
             break

    # 6. NOMBRE TERCERO
    for i, line in enumerate(lines):
        if "USUARIO" in line.upper():
             parts = line.split("RUC")
             if len(parts) > 1:
                 name = re.sub(r'[\d\s:-]+', ' ', parts[1]).strip()
                 if len(name) > 4: data["nombre_tercero"] = name
             elif i + 1 < len(lines):
                 if "nombre_tercero" not in data:
                     data["nombre_tercero"] = lines[i+1].strip()

    # 7. MONTO
    monto_paren = re.search(r'\(\s*([\dOIZSB]{1,6}[\.,]\d{2})\s*\)', text)
    if monto_paren:
        data["monto"] = monto_paren.group(1).replace('O','0').replace('S','5')
    
    monto_soles = re.search(r'(?:S/|Soles)\.?\s*([\d\.,]+)', text)
    if monto_soles and "monto" not in data:
         data["monto"] = monto_soles.group(1)

    # 8. FECHAS
    all_dates = re.findall(r'\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b', text)
    fecha_label_match = re.search(r'(?i)FECHA\s*[:\.]?[\s\n]*(\d{1,2}[/-]\d{1,2}[/-]20\d{2})', text)
    if fecha_label_match:
        data["fecha_recepcion"] = fecha_label_match.group(1).replace('-', '/')
    elif all_dates:
        d, m, y = all_dates[0]
        data["fecha_recepcion"] = f"{d}/{m}/{y}"

    meses_pattern = r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)'
    date_text_match = re.search(rf'(\d{{1,2}})\s+de\s+{meses_pattern}\s+del?\s+(20\d{{2}})', text, re.IGNORECASE)
    if date_text_match:
        d = date_text_match.group(1)
        m_txt = date_text_match.group(2).lower()
        y = date_text_match.group(3)
        meses_map = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", 
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08", 
            "septiembre": "09", "setiembre": "09", "octubre": "10", 
            "noviembre": "11", "diciembre": "12"
        }
        data["fecha_rc"] = f"{d.zfill(2)}/{meses_map[m_txt]}/{y}"
    
    if "fecha_rc" not in data and len(all_dates) > 1:
         d, m, y = all_dates[1]
         curr = f"{d}/{m}/{y}"
         if curr != data.get("fecha_recepcion"):
             data["fecha_rc"] = curr

    # 9. CHEQUE / BOLETA
    cheque_match = re.search(r'\b(\d{8}-\d)\b', text)
    if cheque_match:
        data["cheque_boleta"] = cheque_match.group(1)

    return data

# --- WebSocket Helper ---
class WebSocketManager:
    def __init__(self):
        self.clients: List[WebSocketServer] = []
    def register(self, ws: WebSocketServer):
        self.clients.append(ws)
    def unregister(self, ws: WebSocketServer):
        if ws in self.clients: self.clients.remove(ws)
    def broadcast(self, message: dict):
        self.clients = [client for client in self.clients if client.connected]
        for client in self.clients:
            try:
                import json
                client.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error enviando WS: {e}")
ws_manager = WebSocketManager()

# --- Rutas ---

@app.route("/", methods=["GET"])
def index():
    ip = get_ip()
    port = 8000
    mobile_url = f"http://{ip}:{port}/mobile"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(mobile_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return render_template("desktop.html", qr_code=img_str, mobile_url=mobile_url)

@app.route("/mobile", methods=["GET"])
def mobile():
    return render_template("mobile.html")

@sock.route('/ws/desktop')
def desktop_sock(ws):
    ws_manager.register(ws)
    try:
        while True:
            data = ws.receive()
            if data == 'ping': pass
    except Exception:
        pass
    finally:
        ws_manager.unregister(ws)

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    try:
        image_bytes = file.read()
        original_image = Image.open(io.BytesIO(image_bytes))
        
        try:
            image = ImageOps.exif_transpose(original_image)
        except Exception:
            image = original_image

        # 1. Preprocesamiento SIMPLE (El que funcionaba bien)
        processed_image = preprocess_image(image)
        
        img_str = to_base64_img(processed_image)

        # 2. OCR Loop
        rotations = [0, 180, 270, 90]
        best_data = {}
        best_text = ""
        max_score = -1 

        for angle in rotations:
            if angle == 0:
                img_to_process = processed_image
            else:
                img_to_process = processed_image.rotate(angle, expand=True)

            custom_config = r'--oem 3 --psm 6' 
            text = pytesseract.image_to_string(img_to_process, config=custom_config)
            
            data = extract_data_from_text(text)
            
            score = 0
            if "exp_sigad" in data: score += 5
            if "ruc_contribuyente" in data: score += 4
            if "res_coactiva" in data: score += 4
            score += len(data) 
            
            logger.info(f"Rotación {angle}° - Score: {score} - Datos: {data}")

            if score > max_score:
                max_score = score
                best_data = data
                best_text = f"[Rotación {angle}°]\n" + text
            
            if score >= 15: 
                break
        
        final_data = {
            "exp_sigad": best_data.get("exp_sigad", ""),
            "fecha_recepcion": best_data.get("fecha_recepcion", ""),
            "ruc_contribuyente": best_data.get("ruc_contribuyente", ""),
            "nombre_contribuyente": best_data.get("nombre_contribuyente", ""),
            "res_coactiva": best_data.get("res_coactiva", ""),
            "fecha_rc": best_data.get("fecha_rc", ""),
            "expediente_rc": best_data.get("expediente_rc", ""),
            "monto": best_data.get("monto", ""),
            "ruc_tercero": best_data.get("ruc_tercero", ""),
            "nombre_tercero": best_data.get("nombre_tercero", ""),
            "cheque_boleta": best_data.get("cheque_boleta", "")
        }

        message = {
            "type": "new_scan",
            "data": final_data,
            "raw_text": best_text,
            "processed_image": img_str
        }
        ws_manager.broadcast(message)

        return jsonify({"status": "success", "data": final_data})

    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    ip = get_ip()
    print(f"--- SERVIDOR FLASK (Sweet Spot) ---")
    print(f"URL PC: http://{ip}:8000")
    print(f"URL Local: http://127.0.0.1:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
