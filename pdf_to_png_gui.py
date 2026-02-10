"""
PDF to PNG Converter - Interfaz Gráfica (Sin Poppler)
Usa PyMuPDF (fitz) - No requiere Poppler
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from PIL import Image
import threading

class PDFtoPNGConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("🖼️ PDF to PNG Converter")
        self.root.geometry("700x600")
        self.root.configure(bg="#f0f4f8")
        
        # Variables
        self.pdf_files = []
        self.output_folder = None
        self.dpi_var = tk.IntVar(value=300)
        self.is_converting = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#0163ac", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🖼️ PDF to PNG Converter",
            font=("Segoe UI", 20, "bold"),
            bg="#0163ac",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Main container
        main_frame = tk.Frame(self.root, bg="#f0f4f8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sección de selección de archivos
        file_section = tk.LabelFrame(
            main_frame,
            text="📁 Archivos PDF",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#0163ac",
            relief=tk.FLAT,
            borderwidth=2
        )
        file_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Botones de selección
        btn_frame = tk.Frame(file_section, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.btn_select_file = tk.Button(
            btn_frame,
            text="📄 Seleccionar Archivo",
            command=self.select_file,
            bg="#0163ac",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.btn_select_file.pack(side=tk.LEFT, padx=5)
        
        self.btn_select_folder = tk.Button(
            btn_frame,
            text="📂 Seleccionar Carpeta",
            command=self.select_folder,
            bg="#a91e5c",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.btn_select_folder.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = tk.Button(
            btn_frame,
            text="🗑️ Limpiar",
            command=self.clear_files,
            bg="#64748b",
            fg="white",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.btn_clear.pack(side=tk.RIGHT, padx=5)
        
        # Lista de archivos
        self.file_listbox = tk.Listbox(
            file_section,
            font=("Consolas", 9),
            bg="#f8fafc",
            fg="#1e293b",
            selectbackground="#0163ac",
            selectforeground="white",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Configuración
        config_section = tk.LabelFrame(
            main_frame,
            text="⚙️ Configuración",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#0163ac",
            relief=tk.FLAT,
            borderwidth=2
        )
        config_section.pack(fill=tk.X, pady=(0, 10))
        
        config_inner = tk.Frame(config_section, bg="white")
        config_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Carpeta de salida
        tk.Label(
            config_inner,
            text="📁 Carpeta de salida:",
            font=("Segoe UI", 10),
            bg="white",
            fg="#334155"
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.output_label = tk.Label(
            config_inner,
            text="(Misma carpeta del PDF)",
            font=("Segoe UI", 9, "italic"),
            bg="white",
            fg="#64748b"
        )
        self.output_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        self.btn_output = tk.Button(
            config_inner,
            text="Cambiar",
            command=self.select_output_folder,
            bg="#e2e8f0",
            fg="#334155",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.btn_output.grid(row=0, column=2, padx=5)
        
        # DPI
        tk.Label(
            config_inner,
            text="🎯 Calidad (DPI):",
            font=("Segoe UI", 10),
            bg="white",
            fg="#334155"
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        dpi_frame = tk.Frame(config_inner, bg="white")
        dpi_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=10)
        
        for dpi, label in [(150, "Básica"), (300, "Alta ⭐"), (600, "Muy Alta")]:
            tk.Radiobutton(
                dpi_frame,
                text=f"{dpi} - {label}",
                variable=self.dpi_var,
                value=dpi,
                font=("Segoe UI", 9),
                bg="white",
                fg="#334155",
                selectcolor="#e4f3ff",
                activebackground="white"
            ).pack(side=tk.LEFT, padx=10)
        
        # Botón de conversión
        self.btn_convert = tk.Button(
            main_frame,
            text="🚀 CONVERTIR A PNG",
            command=self.start_conversion,
            bg="#10b981",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor="hand2"
        )
        self.btn_convert.pack(fill=tk.X, pady=(0, 10))
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Log de salida
        log_section = tk.LabelFrame(
            main_frame,
            text="📋 Log de Conversión",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#0163ac",
            relief=tk.FLAT,
            borderwidth=2
        )
        log_section.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = ScrolledText(
            log_section,
            font=("Consolas", 9),
            bg="#1e293b",
            fg="#e2e8f0",
            relief=tk.FLAT,
            borderwidth=0,
            height=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Mensaje inicial
        self.log("✨ Bienvenido al convertidor PDF to PNG (PyMuPDF)")
        self.log("📝 Selecciona uno o más archivos PDF para comenzar\n")
    
    def log(self, message):
        """Agregar mensaje al log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def select_file(self):
        """Seleccionar archivo PDF individual"""
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if files:
            for file in files:
                if file not in self.pdf_files:
                    self.pdf_files.append(file)
                    self.file_listbox.insert(tk.END, os.path.basename(file))
            self.log(f"✅ {len(files)} archivo(s) agregado(s)")
    
    def select_folder(self):
        """Seleccionar carpeta con PDFs"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            pdf_files = list(Path(folder).glob("*.pdf"))
            if pdf_files:
                for file in pdf_files:
                    file_str = str(file)
                    if file_str not in self.pdf_files:
                        self.pdf_files.append(file_str)
                        self.file_listbox.insert(tk.END, file.name)
                self.log(f"✅ {len(pdf_files)} PDF(s) encontrado(s) en la carpeta")
            else:
                messagebox.showwarning("Sin PDFs", "No se encontraron archivos PDF en la carpeta seleccionada")
    
    def clear_files(self):
        """Limpiar lista de archivos"""
        self.pdf_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.log("🗑️ Lista de archivos limpiada")
    
    def select_output_folder(self):
        """Seleccionar carpeta de salida"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_folder = folder
            self.output_label.config(text=f"...{folder[-40:]}")
            self.log(f"📁 Carpeta de salida: {folder}")
    
    def start_conversion(self):
        """Iniciar conversión en un hilo separado"""
        if not self.pdf_files:
            messagebox.showwarning("Sin archivos", "Por favor selecciona al menos un archivo PDF")
            return
        
        if self.is_converting:
            messagebox.showinfo("En proceso", "Ya hay una conversión en progreso")
            return
        
        # Iniciar conversión en hilo separado
        thread = threading.Thread(target=self.convert_pdfs, daemon=True)
        thread.start()
    
    def convert_pdfs(self):
        """Convertir todos los PDFs seleccionados usando PyMuPDF"""
        self.is_converting = True
        self.btn_convert.config(state=tk.DISABLED, bg="#64748b")
        self.progress.start()
        
        # Verificar PyMuPDF
        try:
            import fitz  # PyMuPDF
        except ImportError:
            self.log("❌ Error: PyMuPDF no está instalado")
            self.log("   Ejecuta: pip install PyMuPDF")
            self.progress.stop()
            self.btn_convert.config(state=tk.NORMAL, bg="#10b981")
            self.is_converting = False
            messagebox.showerror(
                "PyMuPDF Requerido",
                "PyMuPDF no está instalado.\n\nEjecuta:\npip install PyMuPDF"
            )
            return
        
        dpi = self.dpi_var.get()
        zoom = dpi / 72  # 72 DPI es la resolución base de PDF
        total_files = len(self.pdf_files)
        successful = 0
        
        self.log("\n" + "="*60)
        self.log(f"🚀 Iniciando conversión de {total_files} archivo(s)")
        self.log(f"🎯 Calidad: {dpi} DPI (zoom: {zoom:.2f}x)")
        self.log("="*60 + "\n")
        
        for i, pdf_path in enumerate(self.pdf_files, 1):
            try:
                self.log(f"📄 [{i}/{total_files}] Procesando: {os.path.basename(pdf_path)}")
                
                # Determinar carpeta de salida
                output_folder = self.output_folder if self.output_folder else str(Path(pdf_path).parent)
                pdf_name = Path(pdf_path).stem
                
                # Abrir PDF
                doc = fitz.open(pdf_path)
                total_pages = len(doc)
                
                # Convertir cada página
                for page_num in range(total_pages):
                    page = doc[page_num]
                    
                    # Crear matriz de transformación para el zoom
                    mat = fitz.Matrix(zoom, zoom)
                    
                    # Renderizar página a imagen
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Nombre del archivo de salida
                    if total_pages == 1:
                        output_path = os.path.join(output_folder, f"{pdf_name}.png")
                    else:
                        output_path = os.path.join(output_folder, f"{pdf_name}_pagina_{page_num + 1}.png")
                    
                    # Guardar como PNG
                    pix.save(output_path)
                    self.log(f"   ✅ Página {page_num + 1}/{total_pages} guardada")
                
                doc.close()
                successful += 1
                self.log(f"   🎉 Completado: {total_pages} imagen(es) generada(s)\n")
                
            except Exception as e:
                self.log(f"   ❌ Error: {str(e)}\n")
        
        self.log("="*60)
        self.log(f"✨ Proceso completado: {successful}/{total_files} archivo(s) convertido(s)")
        self.log("="*60 + "\n")
        
        self.progress.stop()
        self.btn_convert.config(state=tk.NORMAL, bg="#10b981")
        self.is_converting = False
        
        if successful > 0:
            messagebox.showinfo(
                "Conversión Completada",
                f"✅ {successful} de {total_files} archivo(s) convertido(s) exitosamente"
            )
        elif successful == 0 and total_files > 0:
            messagebox.showwarning(
                "Sin Conversiones",
                "No se pudo convertir ningún archivo.\nRevisa el log para más detalles."
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFtoPNGConverter(root)
    root.mainloop()
