import os
import re
import socket
import logging
from typing import List
from fastapi import FastAPI, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import qrcode
import io
import base64
from PIL import Image
import pytesseract

# Configuración de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Montar estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Configuración Tesseract (Intentar encontrarlo en Windows) ---
# Rutas comunes donde podría estar instalado
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
    logger.warning("Tesseract NO encontrado. El OCR fallará si no está en PATH.")

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

from PIL import Image, ImageOps

# ... imports ...

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

def clean_text(text: str):
    """Limpia el texto de ruido común"""
    return text.replace("‘", "").replace("’", "").replace("“", "").replace("”", "").strip()

def extract_data_from_text(text: str):
    """
    Intenta extraer datos de un texto dado.
    """
    data = {}
    
    # 1. RUC: 11 dígitos, permitiendo espacios o guiones
    # Regex: Empieza por 10,15,17,20, seguido de 9 dígitos, permitiendo espacios
    ruc_match = re.search(r'\b(10|15|17|20)[\s-]*(\d[\s-]*){9}\b', text)
    if ruc_match:
        # Limpiar el resultado (quitar espacios y guiones)
        clean_ruc = re.sub(r'[\s-]', '', ruc_match.group(0))
        if len(clean_ruc) == 11:
            data["ruc"] = clean_ruc

    # 2. FECHA: Formatos dd/mm/yyyy, dd-mm-yyyy.
    # A veces el OCR lee 'O' en vez de '0' o 'l' en vez de '1'
    # Intentamos normalizar un poco antes, pero un regex flexible ayuda
    # Rango años: 2020-2030 (ajustable)
    fecha_match = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b', text)
    if fecha_match:
        # Forzar formato dd/mm/yyyy
        data["fecha"] = f"{fecha_match.group(1)}/{fecha_match.group(2)}/{fecha_match.group(3)}"

    # 3. EXPEDIENTE:
    # Busca "Expediente" o "Exp" seguido de código
    # El código suele tener letras, números y guiones: "000-NR009-2026..."
    exp_match = re.search(r'(?i)(expediente|exp\.?|exp)[\s.:º°]*([\w-]+)', text)
    if exp_match:
        data["expediente"] = exp_match.group(2)
        
    # Si no encontró expediente con la palabra clave, busca formato común de expediente largo
    # E.g. 8-6562-9202 (basado en el sample del usuario) 
    # Patrón genérico de expediente judicial/admin: NNNN-NNNN-NNNN...
    if "expediente" not in data:
         # Intenta capturar secuencias largas de números y guiones
         long_code = re.search(r'\b\d+-\d+-\d+-[\w-]+\b', text)
         if long_code:
             data["expediente"] = long_code.group(0)

    return data

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
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
    
    return templates.TemplateResponse("desktop.html", {
        "request": request, 
        "qr_code": img_str, 
        "mobile_url": mobile_url
    })

@app.get("/mobile", response_class=HTMLResponse)
async def read_mobile(request: Request):
    return templates.TemplateResponse("mobile.html", {"request": request})

@app.websocket("/ws/desktop")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file:
        return {"error": "No file uploaded"}
    
    try:
        image_data = await file.read()
        original_image = Image.open(io.BytesIO(image_data))
        
        # 1. Corregir orientación EXIF (típico en móviles)
        try:
            image = ImageOps.exif_transpose(original_image)
        except Exception:
            image = original_image

        # Estrategia de Rotación:
        # Probamos 0 grados, luego 180, luego 90, luego 270.
        # Nos quedamos con el resultado que tenga más datos.
        
        rotations = [0, 180, 270, 90]
        best_data = {}
        best_text = ""
        max_score = -1 # Score basado en campos encontrados

        for angle in rotations:
            if angle == 0:
                img_to_process = image
            else:
                img_to_process = image.rotate(angle, expand=True)

            text = pytesseract.image_to_string(img_to_process)
            data = extract_data_from_text(text)
            
            # Calcular Score: RUC vale 3 ptos, Fecha 2, Expediente 1
            score = 0
            if "ruc" in data: score += 3
            if "fecha" in data: score += 2
            if "expediente" in data: score += 1
            
            logger.info(f"Rotación {angle}° - Score: {score} - Datos: {data}")

            if score > max_score:
                max_score = score
                best_data = data
                best_text = f"[Rotación {angle}° aplicado]\n" + text
            
            # Si encontramos todo, paramos
            if score >= 6: 
                break
        
        # Completar campos faltantes con "No encontrado"
        final_data = {
            "expediente": best_data.get("expediente", "No encontrado"),
            "fecha": best_data.get("fecha", "No encontrada"),
            "ruc": best_data.get("ruc", "No encontrado")
        }

        # Debug: Anexar info de qué rotación ganó
        logger.info(f"GANADOR: Score {max_score} - {final_data}")

        message = {
            "type": "new_scan",
            "data": final_data,
            "raw_text": best_text
        }
        await manager.broadcast(message)
        
        return {"status": "success", "data": final_data}
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    ip = get_ip()
    print(f"--- SERVIDOR INICIADO ---")
    print(f"Abra su navegador en: http://{ip}:8000")
    print(f"O localmente: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
