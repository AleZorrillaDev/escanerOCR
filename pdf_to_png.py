"""
PDF to PNG Converter
Convierte archivos PDF a imágenes PNG de alta calidad
"""

import os
import sys
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image

def pdf_to_png(pdf_path, output_folder=None, dpi=300):
    """
    Convierte un archivo PDF a imágenes PNG
    
    Args:
        pdf_path (str): Ruta al archivo PDF
        output_folder (str): Carpeta de salida (opcional, por defecto usa la misma carpeta del PDF)
        dpi (int): Resolución de las imágenes (por defecto 300 DPI para alta calidad)
    
    Returns:
        list: Lista de rutas a las imágenes PNG generadas
    """
    try:
        # Validar que el archivo existe
        if not os.path.exists(pdf_path):
            print(f"❌ Error: El archivo '{pdf_path}' no existe")
            return []
        
        # Obtener nombre base del PDF
        pdf_name = Path(pdf_path).stem
        
        # Definir carpeta de salida
        if output_folder is None:
            output_folder = Path(pdf_path).parent
        else:
            os.makedirs(output_folder, exist_ok=True)
        
        print(f"📄 Convirtiendo: {pdf_path}")
        print(f"📁 Carpeta de salida: {output_folder}")
        print(f"🎯 Resolución: {dpi} DPI")
        
        # Convertir PDF a imágenes
        images = convert_from_path(pdf_path, dpi=dpi)
        
        output_paths = []
        total_pages = len(images)
        
        print(f"📊 Total de páginas: {total_pages}")
        
        # Guardar cada página como PNG
        for i, image in enumerate(images, start=1):
            # Nombre del archivo de salida
            if total_pages == 1:
                output_path = os.path.join(output_folder, f"{pdf_name}.png")
            else:
                output_path = os.path.join(output_folder, f"{pdf_name}_pagina_{i}.png")
            
            # Guardar imagen
            image.save(output_path, 'PNG', optimize=True)
            output_paths.append(output_path)
            
            print(f"✅ Página {i}/{total_pages} guardada: {output_path}")
        
        print(f"\n🎉 ¡Conversión completada! {total_pages} imagen(es) generada(s)")
        return output_paths
        
    except Exception as e:
        print(f"❌ Error durante la conversión: {str(e)}")
        return []


def batch_convert(input_folder, output_folder=None, dpi=300):
    """
    Convierte todos los PDFs de una carpeta a PNG
    
    Args:
        input_folder (str): Carpeta con archivos PDF
        output_folder (str): Carpeta de salida (opcional)
        dpi (int): Resolución de las imágenes
    """
    pdf_files = list(Path(input_folder).glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No se encontraron archivos PDF en '{input_folder}'")
        return
    
    print(f"📂 Encontrados {len(pdf_files)} archivo(s) PDF")
    print("=" * 60)
    
    for pdf_file in pdf_files:
        pdf_to_png(str(pdf_file), output_folder, dpi)
        print("=" * 60)
    
    print(f"\n✨ ¡Proceso completado! {len(pdf_files)} PDF(s) convertido(s)")


if __name__ == "__main__":
    print("=" * 60)
    print("🖼️  PDF to PNG Converter")
    print("=" * 60)
    
    # Modo de uso
    if len(sys.argv) < 2:
        print("\n📖 Uso:")
        print("  python pdf_to_png.py <archivo.pdf>")
        print("  python pdf_to_png.py <archivo.pdf> <carpeta_salida>")
        print("  python pdf_to_png.py <archivo.pdf> <carpeta_salida> <dpi>")
        print("\n📝 Ejemplos:")
        print("  python pdf_to_png.py documento.pdf")
        print("  python pdf_to_png.py documento.pdf ./imagenes")
        print("  python pdf_to_png.py documento.pdf ./imagenes 600")
        print("\n💡 Para convertir todos los PDFs de una carpeta:")
        print("  python pdf_to_png.py --batch <carpeta_entrada> [carpeta_salida] [dpi]")
        sys.exit(1)
    
    # Modo batch
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("❌ Error: Especifica la carpeta de entrada")
            sys.exit(1)
        
        input_folder = sys.argv[2]
        output_folder = sys.argv[3] if len(sys.argv) > 3 else None
        dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 300
        
        batch_convert(input_folder, output_folder, dpi)
    
    # Modo archivo único
    else:
        pdf_path = sys.argv[1]
        output_folder = sys.argv[2] if len(sys.argv) > 2 else None
        dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
        
        pdf_to_png(pdf_path, output_folder, dpi)
