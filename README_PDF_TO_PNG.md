# 🖼️ PDF to PNG Converter

Utilidad para convertir archivos PDF a imágenes PNG de alta calidad.

## 📋 Requisitos

Instala las dependencias necesarias:

```bash
pip install pdf2image pillow
```

**Importante:** También necesitas instalar Poppler:

### Windows

1. Descarga Poppler desde: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extrae el archivo ZIP
3. Agrega la carpeta `bin` al PATH del sistema

### Linux

```bash
sudo apt-get install poppler-utils
```

### macOS

```bash
brew install poppler
```

## 🚀 Uso

### Convertir un solo PDF

```bash
# Convertir con configuración por defecto (300 DPI)
python pdf_to_png.py documento.pdf

# Especificar carpeta de salida
python pdf_to_png.py documento.pdf ./imagenes

# Especificar carpeta de salida y DPI personalizado
python pdf_to_png.py documento.pdf ./imagenes 600
```

### Convertir múltiples PDFs (modo batch)

```bash
# Convertir todos los PDFs de una carpeta
python pdf_to_png.py --batch ./carpeta_pdfs

# Con carpeta de salida personalizada
python pdf_to_png.py --batch ./carpeta_pdfs ./imagenes_salida

# Con DPI personalizado
python pdf_to_png.py --batch ./carpeta_pdfs ./imagenes_salida 600
```

## ⚙️ Parámetros

- **pdf_path**: Ruta al archivo PDF a convertir
- **output_folder**: (Opcional) Carpeta donde guardar las imágenes PNG
- **dpi**: (Opcional) Resolución de las imágenes (por defecto 300 DPI)
  - 150 DPI: Calidad básica
  - 300 DPI: Alta calidad (recomendado)
  - 600 DPI: Muy alta calidad (archivos grandes)

## 📝 Ejemplos

```bash
# Convertir factura.pdf a PNG en la misma carpeta
python pdf_to_png.py factura.pdf

# Convertir con alta resolución
python pdf_to_png.py documento.pdf ./salida 600

# Convertir todos los PDFs de una carpeta
python pdf_to_png.py --batch ./documentos ./imagenes
```

## 📤 Salida

- Si el PDF tiene **1 página**: `nombre_archivo.png`
- Si el PDF tiene **múltiples páginas**: `nombre_archivo_pagina_1.png`, `nombre_archivo_pagina_2.png`, etc.

## 💡 Características

✅ Conversión de alta calidad  
✅ Soporte para PDFs de múltiples páginas  
✅ Modo batch para procesar carpetas completas  
✅ DPI configurable  
✅ Optimización automática de imágenes  
✅ Interfaz de línea de comandos amigable

## 🔧 Integración con el proyecto

Este script es independiente y puede usarse por separado del sistema OCR principal.
