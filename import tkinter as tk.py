import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import hashlib
import requests
import subprocess
import threading
import json
import logging
import time  
import webbrowser
from tkinter import simpledialog

# Configuraciones globales
DEFAULT_PAK_FOLDER = r"C:\Program Files (x86)\Steam\steamapps\common\The Isle\TheIsle\Content\Paks"
CONFIG_FILE = "config.json"
SERVERS_FILE = "servers.json"
LOG_FILE = "launcher.log"
LEGACY_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\The Isle"
STEAM_APPID = "376210"
DEFAULT_LEGACY_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\The Isle"
STEAM_URL_PROTOCOL = "steam://run/376210//"
MODS_URL = "https://raw.githubusercontent.com/Nayang0/theisle-mods/main/mods.txt"  # URL donde estará el mods.txt del servidor

# Configurar logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class IsleLauncher:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("The Isle: Legacy Launcher")
            
            # Aumentar el tamaño inicial de la ventana
            self.root.geometry("800x700")
            self.root.resizable(True, True)
            self.root.minsize(800, 700)
            
            # Inicializar pak_folder como None para forzar configuración
            self.pak_folder = None
            
            # Inicializar variables
            self.downloading = False
            self.mod_list = {}
            self.servers = {}
            
            # Cargar configuración
            self.load_config()
            
            # Configurar carpetas
            self.setup_folders()
            
            # Interfaz gráfica
            self.setup_gui()
            
            # Cargar servidores
            self.load_servers()
            
        except Exception as e:
            logging.error(f"Error en inicialización: {str(e)}")
            messagebox.showerror("Error", f"Error al iniciar: {str(e)}")

    def setup_gui(self):
        try:
            # Crear un canvas principal con scrollbar
            canvas = tk.Canvas(self.root)
            scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
            
            # Frame principal scrollable
            scrollable_frame = ttk.Frame(canvas)
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            # Crear ventana en el canvas
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Configurar grid
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

            # Hacer que el canvas se expanda
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            # Frame principal (ahora dentro del scrollable_frame)
            main_frame = ttk.Frame(scrollable_frame, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # Lista de servidores (ahora es el primer elemento)
            ttk.Label(main_frame, text="Servidores Guardados:").grid(row=0, column=0, columnspan=2, sticky=tk.W)
            self.server_listbox = tk.Listbox(main_frame, height=5)
            self.server_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            self.server_listbox.bind('<<ListboxSelect>>', self.on_server_select)
            
            # IP del servidor
            ttk.Label(main_frame, text="IP del Servidor:").grid(row=2, column=0, sticky=tk.W)
            self.ip_entry = ttk.Entry(main_frame, width=30)
            self.ip_entry.grid(row=2, column=1, padx=5, pady=5)
            
            # Lista de mods
            ttk.Label(main_frame, text="Botones Disponibles:").grid(row=4, column=0, columnspan=2, sticky=tk.W)
            self.mod_frame = ttk.Frame(main_frame)
            self.mod_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))

            # Botones
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=6, column=0, columnspan=2, pady=5)

            # Primera fila de botones
            ttk.Button(button_frame, text="Actualizar Mods", 
                      command=self.refresh_mods).grid(row=0, column=0, padx=5, pady=5)
            ttk.Button(button_frame, text="Descargar Mods", 
                      command=self.download_pending_mods).grid(row=0, column=1, padx=5, pady=5)
            ttk.Button(button_frame, text="Conectar", 
                      command=self.connect).grid(row=0, column=2, padx=5, pady=5)

            # Segunda fila de botones
            ttk.Button(button_frame, text="Verificar Servidor", 
                      command=self.verify_server).grid(row=1, column=0, padx=5, pady=5)
            ttk.Button(button_frame, text="Guardar Servidor", 
                      command=self.save_server).grid(row=1, column=1, padx=5, pady=5)
            ttk.Button(button_frame, text="Ver Log", 
                      command=self.view_log).grid(row=1, column=2, padx=5, pady=5)

            # Tercera fila de botones (configuración)
            ttk.Button(button_frame, text="Configurar Legacy", 
                      command=self.set_legacy_path).grid(row=2, column=0, padx=5, pady=5)
            ttk.Button(button_frame, text="Configurar Paks", 
                      command=self.set_paks_path).grid(row=2, column=1, padx=5, pady=5)
            ttk.Button(button_frame, text="Abrir Carpeta Paks", 
                      command=self.open_pak_folder).grid(row=2, column=2, padx=5, pady=5)

            # Después de los botones, añadir marco de ayuda
            help_frame = ttk.LabelFrame(main_frame, text="Guía de Botones", padding="5")
            help_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

            # Textos de ayuda para cada botón
            helps = [
                ("Verificar Servidor", "Analiza si el servidor requiere mods y muestra su estado"),
                ("Actualizar Mods", "Verifica el estado de los mods instalados"),
                ("Descargar Mods", "Descarga los mods faltantes o desactualizados"),
                ("Conectar", "Inicia el juego y conecta al servidor seleccionado"),
                ("Guardar Servidor", "Guarda la IP actual en la lista de servidores"),
                ("Ver Log", "Muestra el registro de errores y eventos"),
                ("Configurar Legacy", "Selecciona la ubicación del ejecutable de Legacy"),
                ("Configurar Paks", "Selecciona la carpeta donde se instalan los mods"),
                ("Abrir Carpeta Paks", "Abre la carpeta donde están los mods instalados")
            ]

            # Crear grid de ayuda (4 columnas)
            for i, (button, help_text) in enumerate(helps):
                row = i // 2  # Dos filas
                col = i % 2   # Dos columnas
                help_label = ttk.Label(help_frame, 
                                    text=f"{button}: {help_text}", 
                                    wraplength=350,
                                    justify=tk.LEFT)
                help_label.grid(row=row, column=col, padx=5, pady=2, sticky=tk.W)

            # Después del marco de ayuda, añadir marco de tutorial
            tutorial_frame = ttk.LabelFrame(main_frame, text="Tutorial de Uso", padding="5")
            tutorial_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

            # Pasos del tutorial
            tutorial_steps = [
                ("Paso 1", "Configura la carpeta Paks usando 'Configurar Paks' (Importante)"),
                ("Paso 2", "Configura la ruta de Legacy usando 'Configurar Legacy' (Importante)"),
                ("Paso 3", "Ingresa la IP del servidor o selecciona uno guardado"),
                ("Paso 4", "Usa 'Verificar Servidor' para comprobar si necesita mods"),
                ("Paso 5", "Si requiere mods, usa 'Actualizar Mods' y luego 'Descargar Mods'"),
                ("Paso 6", "Una vez todo esté listo, presiona 'Conectar' para unirte al servidor")
            ]

            # Crear grid de tutorial
            for i, (step, desc) in enumerate(tutorial_steps):
                step_label = ttk.Label(
                    tutorial_frame, 
                    text=f"➤ {step}: {desc}", 
                    wraplength=700,
                    justify=tk.LEFT
                )
                step_label.grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)

            # Añadir marco de mods disponibles
            mods_help_frame = ttk.LabelFrame(main_frame, text="Guía de Mods Disponibles", padding="5")
            mods_help_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

            # Información de mods
            mods_info = [
                ("TheIsle-Zzz_Yutty.pak/.sig", "es un ejemplo de como se verian Los Mods requeridos para algunos servidores."),
                # Eliminar las otras entradas que no usamos
            ]

            for i, (mod_name, description) in enumerate(mods_info):
                ttk.Label(
                    mods_help_frame,
                    text=f"• {mod_name}: {description}",
                    wraplength=700,
                    justify=tk.LEFT
                ).grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)

            # Configurar el scrolling con el mouse
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        except Exception as e:
            logging.error(f"Error en setup_gui: {str(e)}")
            messagebox.showerror("Error", f"Error en la interfaz: {str(e)}")

    def refresh_mods(self):
        try:
            # Obtiene IP del cuadro de entrada
            ip_port = self.ip_entry.get().strip()
            if not ip_port:
                messagebox.showinfo("Info", "Selecciona un servidor primero")
                return
            
            # Usa esta IP para buscar los mods
            server_mods = self.get_server_mods(ip_port)
            if not server_mods:
                messagebox.showwarning(
                    "Error", 
                    f"No se pudo obtener la lista de mods del servidor {ip_port}"
                )
                return
                
            # Actualizar interfaz con los mods requeridos
            self.update_mod_list(server_mods)
            
        except Exception as e:
            logging.error(f"Error actualizando mods: {str(e)}")
            messagebox.showerror("Error", f"Error al actualizar mods: {str(e)}")

    def check_mod_status(self, filename, expected_hash):
        """Verifica el estado de un mod"""
        try:
            filepath = os.path.join(self.pak_folder, filename)
            
            # Log para debugging
            logging.info(f"Verificando archivo en: {filepath}")
            
            if not os.path.exists(filepath):
                logging.info(f"Archivo no encontrado en: {filepath}")
                return "No instalado"
            
            # Leer archivo y generar hash
            with open(filepath, 'rb') as f:
                file_content = f.read()
                current_hash = hashlib.sha256(file_content).hexdigest().lower()
                expected_hash = expected_hash.lower()
            
            # Log detallado
            logging.info(f"Verificando {filename}")
            logging.info(f"Hash esperado: {expected_hash}")
            logging.info(f"Hash actual: {current_hash}")
            logging.info(f"¿Hashes coinciden?: {current_hash == expected_hash}")
            
            # Comparación exacta de hashes
            if current_hash == expected_hash:
                return "Verificado"
            else:
                logging.warning(f"Hash no coincide para {filename}")
                logging.warning(f"Esperado: {expected_hash}")
                logging.warning(f"Actual: {current_hash}")
                return "Desactualizado"
            
        except Exception as e:
            logging.error(f"Error verificando {filename}: {str(e)}")
            return "Error al verificar"

    def generate_hashes(self):
        """Genera hashes para los archivos en la carpeta mods"""
        mods_directory = os.path.join(os.path.dirname(__file__), 'mods')
        
        # URLs de Google Drive
        DRIVE_URLS = {
            'TheIsle-Zzz_Yutty.pak': 'https://drive.google.com/uc?export=download&id=1o4p0B4NFdRUReQh5Z4wYPx457SJne_oE',
            'TheIsle-Zzz_Yutty.sig': 'https://drive.google.com/uc?export=download&id=1wbeqgcmNn7gIR8BCRiBbz62rV1Typjbq'
        }
        
        # Crear la carpeta mods si no existe
        if not os.path.exists(mods_directory):
            os.makedirs(mods_directory)
            messagebox.showinfo("Info", f"Carpeta 'mods' creada en:\n{mods_directory}\n\nPor favor, coloca tus archivos .pak y .sig en esta carpeta")
            return

        # Verificar si hay archivos
        if not any(f.endswith(('.pak', '.sig')) for f in os.listdir(mods_directory)):
            messagebox.showwarning("Advertencia", f"No se encontraron archivos .pak o .sig en:\n{mods_directory}")
            return

        try:
            # Generar mods.txt con URLs reales
            with open('mods.txt', 'w') as f:
                f.write("# filename hash download_url\n")
                for filename in os.listdir(mods_directory):
                    if filename.endswith(('.pak', '.sig')):
                        filepath = os.path.join(mods_directory, filename)
                        with open(filepath, 'rb') as file:
                            file_hash = hashlib.sha256(file.read()).hexdigest()
                        # Usar URL real de Google Drive si está disponible
                        download_url = DRIVE_URLS.get(filename, '')
                        if download_url:
                            f.write(f"{filename} {file_hash} {download_url}\n")
                        else:
                            logging.warning(f"No se encontró URL para {filename}")
            
            messagebox.showinfo("Éxito", "Archivo mods.txt generado exitosamente!")
            self.refresh_mods()  # Actualizar la lista de mods
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar hashes: {str(e)}")

    # Modificar el método connect para usar la ruta configurada
    def connect(self):
        try:
            ip = self.ip_entry.get().strip()
            if not ip or ':' not in ip:
                messagebox.showerror("Error", "Por favor ingresa una IP de servidor")
                return

            # Verificar solo la ruta de Legacy
            game_exe = os.path.join(self.legacy_path, "TheIsle.exe")
            if not os.path.exists(game_exe):
                messagebox.showerror("Error", "No se encuentra TheIsle.exe en la ruta configurada")
                return

            # Lanzar el juego directamente
            command = f'"{game_exe}" -log -USEALLAVAILABLECORES +connect {ip} +accept_responsibility -nosteam -game'
            logging.info(f"Lanzando Legacy: {command}")
            
            subprocess.Popen(command, shell=True, cwd=self.legacy_path)

        except Exception as e:
            logging.error(f"Error al conectar: {str(e)}")
            messagebox.showerror("Error", f"Error al conectar: {str(e)}")

    def download_mods(self, mod_list):
        """Descarga los mods requeridos desde Google Drive"""
        try:
            if not self.pak_folder:
                raise Exception("La carpeta Paks no está configurada")

            for mod_name in mod_list:
                if mod_name not in self.mod_list:
                    raise Exception(f"Mod no encontrado en la lista: {mod_name}")
                    
                mod_info = self.mod_list[mod_name]
                url = mod_info['url']
                
                logging.info(f"Descargando {mod_name} desde {url}")
                
                # Manejar URL de Google Drive
                if 'drive.google.com' in url:
                    try:
                        # Extraer ID de Google Drive
                        file_id = url.split('id=')[1].split('&')[0]
                        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                        
                        # Primera solicitud para manejar archivos grandes
                        session = requests.Session()
                        response = session.get(download_url, stream=True)
                        
                        # Manejar confirmación para archivos grandes
                        for key, value in response.cookies.items():
                            if key.startswith('download_warning'):
                                download_url += f"&confirm={value}"
                                response = session.get(download_url, stream=True)
                                break
                                
                    except Exception as e:
                        raise Exception(f"Error procesando URL de Google Drive: {str(e)}")
                else:
                    response = requests.get(url, stream=True)
                
                # Descargar archivo
                filepath = os.path.join(self.pak_folder, mod_name)
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verificar hash después de la descarga
                status = self.check_mod_status(mod_name, mod_info['hash'])
                logging.info(f"Estado después de descarga: {status}")
                
                if status != "Verificado":
                    raise Exception(f"Hash no coincide para {mod_name}")
                
                # Actualizar estado en la interfaz
                mod_info['status_label'].config(text="Verificado")
                
                # Forzar actualización visual
                self.root.update()
            
            messagebox.showinfo("Éxito", "Mods descargados y verificados correctamente")
            
        except Exception as e:
            logging.error(f"Error descargando mods: {str(e)}")
            messagebox.showerror("Error", f"Error al descargar mods: {str(e)}")
            return False
        
        return True

    def download_file(self, filename, url, is_sig=False):
        """Descarga mejorada desde Google Drive"""
        try:
            if 'drive.google.com' in url:
                file_id = url.split('id=')[1].split('&')[0]
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                
                session = requests.Session()
                response = session.get(download_url, stream=True)
                
                # Manejar confirmación para archivos grandes
                for key, value in response.cookies.items():
                    if key.startswith('download_warning'):
                        download_url += f"&confirm={value}"
                        response = session.get(download_url, stream=True)
                        break
            else:
                response = requests.get(url, stream=True)

            filepath = os.path.join(self.pak_folder, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            return True
        except Exception as e:
            logging.error(f"Error descargando {filename}: {str(e)}")
            return False

    def download_pending_mods(self):
        """Descarga los mods pendientes"""
        try:
            if not self.pak_folder:
                messagebox.showwarning(
                    "Configuración Requerida",
                    "Primero configura la carpeta Paks usando el botón 'Configurar Paks'"
                )
                return
                
            # Buscar mods no instalados o desactualizados
            pending_mods = []
            for filename, mod_info in self.mod_list.items():
                status = self.check_mod_status(filename, mod_info['hash'])
                if status in ["No instalado", "Desactualizado"]:
                    pending_mods.append(filename)
                    
            if not pending_mods:
                messagebox.showinfo("Info", "No hay mods pendientes de descargar")
                return
                
            # Preguntar antes de descargar
            if messagebox.askyesno(
                "Descargar Mods", 
                f"Se encontraron {len(pending_mods)} mods pendientes. ¿Descargar ahora?"
            ):
                self.download_mods(pending_mods)
                
        except Exception as e:
            logging.error(f"Error al descargar mods pendientes: {str(e)}")
            messagebox.showerror("Error", f"Error al descargar mods: {str(e)}")

    # 1. Configuración persistente
    def load_config(self):
        """Carga la configuración del launcher"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    # No usar valor por defecto, forzar configuración manual
                    self.pak_folder = config.get("pak_folder", None)
                    self.legacy_path = config.get("legacy_path", DEFAULT_LEGACY_PATH)
            else:
                self.pak_folder = None
                self.legacy_path = DEFAULT_LEGACY_PATH
                self.save_config()
        except Exception as e:
            logging.error(f"Error al cargar configuración: {str(e)}")
            self.pak_folder = None

    # Añadir método para guardar configuración
    def save_config(self):
        """Guarda la configuración del launcher"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    "pak_folder": self.pak_folder,
                    "legacy_path": self.legacy_path
                }, f, indent=4)
        except Exception as e:
            logging.error(f"Error al guardar configuración: {str(e)}")

    # Añadir método para seleccionar ruta de Legacy
    def set_legacy_path(self):
        """Permite al usuario seleccionar la ubicación de The Isle Legacy"""
        try:
            filepath = filedialog.askopenfilename(
                title="Seleccionar TheIsle.exe (Legacy)",
                initialdir=os.path.dirname(self.legacy_path),
                filetypes=[("Ejecutable", "TheIsle.exe")]
            )
            if filepath and  os.path.exists(filepath):
                self.legacy_path = os.path.dirname(filepath)
                self.save_config()
                messagebox.showinfo("Éxito", "Ruta de Legacy actualizada correctamente")
        except Exception as e:
            logging.error(f"Error al establecer ruta de Legacy: {str(e)}")

    # Añadir método para seleccionar ruta de Paks
    def set_paks_path(self):
        """Permite al usuario seleccionar la ubicación de la carpeta Paks"""
        try:
            folder_path = filedialog.askdirectory(
                title="Seleccionar carpeta Paks",
                initialdir=self.pak_folder
            )
            if folder_path:
                self.pak_folder = folder_path
                self.save_config()
                messagebox.showinfo("Éxito", "Ruta de Paks actualizada correctamente")
        except Exception as e:
            logging.error(f"Error al establecer ruta de Paks: {str(e)}")

    # 2. Carpeta para mods deshabilitados
    def setup_folders(self):
        self.disabled_folder = os.path.join(self.pak_folder, "Disabled")
        if not os.path.exists(self.disabled_folder):
            os.makedirs(self.disabled_folder)

    # 3. Botón para abrir carpeta
    def open_pak_folder(self):
        os.startfile(self.pak_folder)

    def load_servers(self):
        """Carga la lista de servidores con más información"""
        try:
            if os.path.exists(SERVERS_FILE):
                with open(SERVERS_FILE, 'r') as f:
                    self.servers = json.load(f)
                self.server_listbox.delete(0, tk.END)
                for ip in self.servers:
                    info = self.servers[ip]
                    display = f"{info.get('name', 'Unknown')} - {ip}"
                    self.server_listbox.insert(tk.END, display)
        except Exception as e:
            logging.error(f"Error cargando servidores: {str(e)}")

    def save_server(self):
        """Guarda el servidor actual en la lista usando la verificación"""
        try:
            ip = self.ip_entry.get().strip()
            if not ip or ':' not in ip:
                messagebox.showerror("Error", "IP inválida")
                return
                
            ip_address = ip.split(':')[0]
            port = ip.split(':')[1]
            
            # Detectar tipo usando la misma lógica que verify_server
            server_type = "Local" if any(ip_address.startswith(prefix) for prefix in [
                '127.0.0.1',
                'localhost',
                '192.168.',
                '190.',  # Añadir rango 190
                '10.'
            ] + [f'172.{i}.' for i in range(16, 32)]) else "Web"

            # Verificar mods.txt y estado
            has_mods = False
            if os.path.exists('mods.txt'):
                with open('mods.txt', 'r') as f:
                    content = f.read().strip()
                    if content and not content.startswith('#'):
                        has_mods = True

            # Generar nombre descriptivo
            if has_mods:
                server_name = f"Servidor {server_type} con Mods ({port})"
            else:
                server_name = f"Servidor {server_type} ({port})"
            
            # Guardar servidor con información
            self.servers[ip] = {
                "name": server_name,
                "type": server_type,
                "has_mods": has_mods,
                "last_used": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Guardar en archivo
            with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.servers, f, indent=4, ensure_ascii=False)
            
            # Actualizar lista
            self.update_server_list()
            messagebox.showinfo("Éxito", f"Servidor guardado como: {server_name}")
                
        except Exception as e:
            logging.error(f"Error al guardar servidor: {str(e)}")
            messagebox.showerror("Error", f"Error al guardar servidor: {str(e)}")

    def detect_server_type(self, ip):
        """Detecta si un servidor es local o web"""
        local_ips = [
            '127.0.0.1',
            'localhost',
            '192.168.',
            '190.',  # Añadir rango 190
            '10.',
            '172.16.',
            '172.17.',
            '172.18.',
            '172.19.',
            '172.20.',
            '172.21.',
            '172.22.',
            '172.23.',
            '172.24.',
            '172.25.',
            '172.26.',
            '172.27.',
            '172.28.',
            '172.29.',
            '172.30.',
            '172.31.'
        ]
        
        for local_ip in local_ips:
            if ip.startswith(local_ip):
                return "Local"
        return "Web"

    def save_last_server(self):
        """Guarda información del último servidor usado"""
        try:
            with open("last_server.json", 'w') as f:
                json.dump({
                    "ip": self.ip_entry.get().strip(),
                    "mods": list(self.mod_list.keys()),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }, f, indent=4)
        except Exception as e:
            logging.error(f"Error guardando último servidor: {str(e)}")

    def on_server_select(self, event):
        """Maneja la selección de un servidor"""
        try:
            selection = self.server_listbox.curselection()
            if selection:
                selected_text = self.server_listbox.get(selection[0])
                ip_port = selected_text.split(" - ")[1].strip()
                
                # Actualizar entrada de IP
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, ip_port)
                
                logging.info(f"Servidor seleccionado: {ip_port}")
                self.refresh_mods()
                
        except Exception as e:
            logging.error(f"Error en selección de servidor: {str(e)}")

    def view_log(self):
        """Muestra el archivo de log"""
        try:
            if os.path.exists(LOG_FILE):
                subprocess.Popen(['notepad', LOG_FILE])
            else:
                messagebox.showinfo("Info", "No hay archivo de log disponible")
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir log: {str(e)}")

    def update_server_list(self):
        """Actualiza la lista de servidores en la GUI"""
        try:
            self.server_listbox.delete(0, tk.END)
            for ip in self.servers:
                info = self.servers[ip]
                server_type = info.get('type', 'Desconocido')
                display = f"{info.get('name', 'Unknown')} [{server_type}] - {ip}"
                self.server_listbox.insert(tk.END, display)
        except Exception as e:
            logging.error(f"Error al actualizar lista de servidores: {str(e)}")

    def update_mod_status(self, filename, status):
        """Actualiza el estado visual de un mod"""
        try:
            if filename in self.mod_list:
                self.mod_list[filename]['status_label'].config(text=status)
                self.mod_list[filename]['status'] = status
                # Forzar actualización visual
                self.root.update_idletasks()
        except Exception as e:
            logging.error(f"Error actualizando estado de mod: {str(e)}")

    def toggle_admin_features(self):
        """Habilita/deshabilita características de administrador con verificación de clave"""
        try:
            if self.is_admin.get():
                # Crear diálogo para la clave
                password_dialog = tk.Toplevel(self.root)
                password_dialog.title("Verificación de Administrador")
                password_dialog.geometry("300x150")
                password_dialog.resizable(False, False)
                password_dialog.transient(self.root)
                
                # Centrar la ventana
                password_dialog.geometry("+%d+%d" % (
                    self.root.winfo_rootx() + 50,
                    self.root.winfo_rooty() + 50
                ))
                
                # Frame principal
                main_frame = ttk.Frame(password_dialog, padding="20")
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # Label y entrada para la clave
                ttk.Label(main_frame, text="Ingrese la clave de administrador:").pack(pady=5)
                password_entry = ttk.Entry(main_frame, show="*")
                password_entry.pack(pady=5)
                password_entry.focus()
                
                def verify_password():
                    # Clave de administrador (cámbiala por la que desees)
                    ADMIN_PASSWORD = "AVA"
                    
                    if password_entry.get() == ADMIN_PASSWORD:
                        self.hash_button.config(state='normal')
                        logging.info("Modo administrador activado")
                        password_dialog.destroy()
                    else:
                        messagebox.showerror("Error", "Clave incorrecta")
                        self.is_admin.set(False)
                        password_dialog.destroy()
                
                # Botones
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(pady=10)
                
                ttk.Button(button_frame, text="Aceptar", command=verify_password).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Cancelar", command=lambda: [
                    password_dialog.destroy(),
                    self.is_admin.set(False)
                ]).pack(side=tk.LEFT, padx=5)
                
                # Hacer la ventana modal
                password_dialog.grab_set()
                password_dialog.focus_set()
                password_dialog.wait_window()
                
            else:
                self.hash_button.config(state='disabled')
                logging.info("Modo administrador desactivado")
                
        except Exception as e:
            logging.error(f"Error al cambiar rol: {str(e)}")
            messagebox.showerror("Error", f"Error al cambiar rol: {str(e)}")
            self.is_admin.set(False)

    def get_server_mods(self, ip_port):
        """Obtiene la lista de mods requeridos para un servidor específico"""
        try:
            if not ip_port:
                return None
                
            logging.info(f"Verificando mods para servidor Legacy: {ip_port}")
            
            # Leer archivo mods.txt global
            if os.path.exists('mods.txt'):
                logging.info("Leyendo mods.txt global")
                with open('mods.txt', 'r') as f:
                    mods_content = f.read()
                    if mods_content.strip() and not mods_content.startswith('#'):
                        return mods_content
                        
            logging.info("No se encontraron mods requeridos")
            return "# filename hash download_url\n# Este servidor no requiere mods"
                
        except Exception as e:
            logging.error(f"Error verificando mods para {ip_port}: {str(e)}")
            return None

    def update_mod_list(self, mods_text):
        """Actualiza la lista de mods en la interfaz"""
        try:
            # Limpiar frame de mods
            for widget in self.mod_frame.winfo_children():
                widget.destroy()
            
            # Limpiar diccionario de mods
            self.mod_list.clear()
            
            # Procesar cada línea del archivo mods.txt
            for line in mods_text.splitlines():
                if line.startswith('#') or not line.strip():
                    continue
                    
                try:
                    filename, file_hash, download_url = line.strip().split()
                    
                    # Crear frame para este mod
                    mod_frame = ttk.Frame(self.mod_frame)
                    mod_frame.pack(fill=tk.X, pady=2)
                    
                    # Nombre del mod
                    ttk.Label(mod_frame, text=filename, width=30).pack(side=tk.LEFT, padx=5)
                    
                    # Estado del mod
                    status_label = ttk.Label(mod_frame, text="Verificando...")
                    status_label.pack(side=tk.LEFT, padx=5)
                    
                    # Guardar información del mod
                    self.mod_list[filename] = {
                        'hash': file_hash,
                        'url': download_url,
                        'status_label': status_label
                    }
                    
                    # Verificar estado actual
                    status = self.check_mod_status(filename, file_hash)
                    self.update_mod_status(filename, status)
                    
                except ValueError:
                    logging.warning(f"Línea mal formateada en mods.txt: {line}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error actualizando lista de mods: {str(e)}")
            messagebox.showerror("Error", f"Error al actualizar lista de mods: {str(e)}")

    def verify_server(self):
        """Verifica el estado completo del servidor"""
        try:
            ip = self.ip_entry.get().strip()
            if not ip or ':' not in ip:
                messagebox.showerror("Error", "IP inválida")
                return
                
            ip_address = ip.split(':')[0]
            port = ip.split(':')[1]
            
            # 1. Detectar tipo de servidor
            server_type = "Local" if any(ip_address.startswith(prefix) for prefix in [
                '127.0.0.1', 'localhost', '192.168.', '190.', '10.'
            ] + [f'172.{i}.' for i in range(16, 32)]) else "Web"

            # 2. Verificar carpeta Paks
            if not self.pak_folder:
                messagebox.showwarning("Advertencia", "Configura primero la carpeta Paks")
                return

            # 3. Preparar resultado
            result = [
                f"Tipo de Servidor: {server_type}",
                f"IP: {ip_address}",
                f"Puerto: {port}",
                "\nVerificación de Mods:"
            ]

            # 4. Verificar los archivos físicamente
            pak_exists = os.path.exists(os.path.join(self.pak_folder, "TheIsle-Zzz_Yutty.pak"))
            sig_exists = os.path.exists(os.path.join(self.pak_folder, "TheIsle-Zzz_Yutty.sig"))

            # 5. Verificar si el servidor tiene mods.txt
            requires_mods = False
            if os.path.exists('mods.txt'):
                with open('mods.txt', 'r') as f:
                    content = f.read().strip()
                    if content and not content.startswith('#'):
                        requires_mods = True
                        result.append("\nServidor con Mods:")
                        # Mostrar archivos requeridos
                        result.append("• TheIsle-Zzz_Yutty.pak")
                        result.append("• TheIsle-Zzz_Yutty.sig")
                        result.append("\nEstado de Instalación:")
                        result.append("✓ TheIsle-Zzz_Yutty.pak" if pak_exists else "✗ TheIsle-Zzz_Yutty.pak (Falta)")
                        result.append("✓ TheIsle-Zzz_Yutty.sig" if sig_exists else "✗ TheIsle-Zzz_Yutty.sig (Falta)")
                    else:
                        result.append("\n✓ Este servidor NO requiere mods")
                        result.append("Puedes conectarte directamente")
            else:
                result.append("\n✓ Este servidor NO requiere mods")
                result.append("Puedes conectarte directamente")

            # 6. Mostrar resultados
            if messagebox.askyesno(
                "Verificación Completada",
                "\n".join(result) + "\n\n¿Desea guardar este servidor?"
            ):
                self.save_server()
                
        except Exception as e:
            logging.error(f"Error verificando servidor: {str(e)}")
            messagebox.showerror("Error", f"Error al verificar servidor: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = IsleLauncher(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error fatal en la aplicación: {str(e)}")
        messagebox.showerror("Error Fatal", f"La aplicación no pudo iniciarse: {str(e)}")