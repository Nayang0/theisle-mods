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

# Configuraciones globales
DEFAULT_PAK_FOLDER = r"C:\Program Files (x86)\Steam\steamapps\common\The Isle\TheIsle\Content\Paks"
CONFIG_FILE = "config.json"
SERVERS_FILE = "servers.json"
LOG_FILE = "launcher.log"
LEGACY_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\The Isle"
STEAM_APPID = "376210"
DEFAULT_LEGACY_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\The Isle"
STEAM_URL_PROTOCOL = "steam://run/376210//"
DEFAULT_SERVER = "190.53.190.195:7797"  # Cambia esto por tu servidor predeterminado
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
            self.root.geometry("500x600")
            
            # Establecer pak_folder antes de cualquier otra operación
            self.pak_folder = DEFAULT_PAK_FOLDER
            
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
            # Frame principal
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Lista de servidores
            ttk.Label(main_frame, text="Servidores Guardados:").grid(row=0, column=0, columnspan=2, sticky=tk.W)
            self.server_listbox = tk.Listbox(main_frame, height=5)
            self.server_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            self.server_listbox.bind('<<ListboxSelect>>', self.on_server_select)
            
            # IP del servidor
            ttk.Label(main_frame, text="IP del Servidor:").grid(row=2, column=0, sticky=tk.W)
            self.ip_entry = ttk.Entry(main_frame, width=30)
            self.ip_entry.grid(row=2, column=1, padx=5, pady=5)
            
            # Lista de mods
            ttk.Label(main_frame, text="Mods Disponibles:").grid(row=3, column=0, columnspan=2, sticky=tk.W)
            self.mod_frame = ttk.Frame(main_frame)
            self.mod_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))

            # Botones
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=5, column=0, columnspan=2, pady=5)
            
            ttk.Button(button_frame, text="Generar Hashes", command=self.generate_hashes).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Actualizar Mods", command=self.refresh_mods).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Conectar", command=self.connect).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Abrir Carpeta Paks", command=self.open_pak_folder).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Guardar Servidor", command=self.save_server).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Ver Log", command=self.view_log).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Configurar Legacy", 
                  command=self.set_legacy_path).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            logging.error(f"Error en setup_gui: {str(e)}")
            messagebox.showerror("Error", f"Error en la interfaz: {str(e)}")

    def refresh_mods(self):
        """Actualiza la lista de mods disponibles"""
        try:
            # Usar archivo local en lugar de URL remota
            with open('mods.txt', 'r') as f:
                mods_data = f.readlines()
            
            # Limpiar frame de mods existente
            for widget in self.mod_frame.winfo_children():
                widget.destroy()
            
            # Actualizar lista de mods
            self.mod_list = {}
            for line in mods_data:
                if line.strip() and not line.startswith('#'):
                    filename, hash_value, download_url = line.split()
                    var = tk.BooleanVar()
                    
                    # Crear checkbox y etiqueta de estado
                    frame = ttk.Frame(self.mod_frame)
                    frame.pack(fill=tk.X, pady=2)
                    
                    ttk.Checkbutton(frame, variable=var).pack(side=tk.LEFT)
                    ttk.Label(frame, text=filename).pack(side=tk.LEFT)
                    status_label = ttk.Label(frame, text=self.check_mod_status(filename, hash_value))
                    status_label.pack(side=tk.RIGHT)
                    
                    self.mod_list[filename] = {
                        'var': var,
                        'hash': hash_value,
                        'url': download_url,
                        'status_label': status_label
                    }
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar mods: {str(e)}")

    def check_mod_status(self, filename, expected_hash):
        """Verifica el estado de un mod"""
        filepath = os.path.join(self.pak_folder, filename)
        if not os.path.exists(filepath):
            return "No instalado"
        
        try:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return "Verificado" if file_hash == expected_hash else "Desactualizado"
        except:
            return "Error al verificar"

    def generate_hashes(self):
        """Genera hashes para los archivos en la carpeta mods"""
        mods_directory = os.path.join(os.path.dirname(__file__), 'mods')
        
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
            # Generar mods.txt
            with open('mods.txt', 'w') as f:
                f.write("# filename hash download_url\n")
                for filename in os.listdir(mods_directory):
                    if filename.endswith(('.pak', '.sig')):
                        filepath = os.path.join(mods_directory, filename)
                        with open(filepath, 'rb') as file:
                            file_hash = hashlib.sha256(file.read()).hexdigest()
                        download_url = "https://example.com/" + filename
                        f.write(f"{filename} {file_hash} {download_url}\n")
            
            messagebox.showinfo("Éxito", "Archivo mods.txt generado exitosamente!")
            self.refresh_mods()  # Actualizar la lista de mods
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar hashes: {str(e)}")

    # Modificar el método connect para usar la ruta configurada
    def connect(self):
        try:
            ip = self.ip_entry.get().strip() or DEFAULT_SERVER
            if not ip or ':' not in ip:
                messagebox.showerror("Error", "IP inválida")
                return

            # Descargar mods.txt del servidor si existe
            try:
                response = requests.get(MODS_URL, timeout=5)
                if response.status_code == 200:
                    with open('mods.txt', 'w') as f:
                        f.write(response.text)
                    self.refresh_mods()
                    
                    # Verificar mods requeridos
                    missing_mods = []
                    for filename, mod_info in self.mod_list.items():
                        if self.check_mod_status(filename, mod_info['hash']) != "Verificado":
                            missing_mods.append(filename)

                    if missing_mods:
                        if messagebox.askyesno("Mods Requeridos", 
                            "Se requieren mods. ¿Deseas descargarlos automáticamente?"):
                            self.download_mods(missing_mods)
                        return
            except:
                logging.info("No se pudo obtener mods.txt del servidor")

            # Construir URL de Steam con parámetros de conexión
            launch_params = f"+connect {ip} +accept_responsibility"
            steam_url = f"{STEAM_URL_PROTOCOL}/{launch_params}"
            
            # Lanzar a través de Steam
            webbrowser.open(steam_url)
            
            # Log del comando
            logging.info(f"Lanzando via Steam: {steam_url}")

        except Exception as e:
            logging.error(f"Error al conectar: {str(e)}")
            messagebox.showerror("Error", f"Error al conectar: {str(e)}")

    def download_mods(self, mod_list):
        """Descarga los mods requeridos"""
        try:
            for mod_name in mod_list:
                mod_info = self.mod_list[mod_name]
                url = mod_info['url']
                
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                filepath = os.path.join(self.pak_folder, mod_name)
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
            messagebox.showinfo("Éxito", "Mods descargados correctamente")
            self.refresh_mods()
            
        except Exception as e:
            logging.error(f"Error descargando mods: {str(e)}")
            messagebox.showerror("Error", f"Error al descargar mods: {str(e)}")

    # 1. Configuración persistente
    def load_config(self):
        """Carga la configuración del launcher"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.pak_folder = config.get("pak_folder", DEFAULT_PAK_FOLDER)
                    self.legacy_path = config.get("legacy_path", DEFAULT_LEGACY_PATH)
            else:
                self.pak_folder = DEFAULT_PAK_FOLDER
                self.legacy_path = DEFAULT_LEGACY_PATH
                self.save_config()
        except Exception as e:
            logging.error(f"Error al cargar configuración: {str(e)}")

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
            if filepath and os.path.exists(filepath):
                self.legacy_path = os.path.dirname(filepath)
                self.save_config()
                messagebox.showinfo("Éxito", "Ruta de Legacy actualizada correctamente")
        except Exception as e:
            logging.error(f"Error al establecer ruta de Legacy: {str(e)}")

    # 2. Carpeta para mods deshabilitados
    def setup_folders(self):
        self.disabled_folder = os.path.join(self.pak_folder, "Disabled")
        if not os.path.exists(self.disabled_folder):
            os.makedirs(self.disabled_folder)

    # 3. Botón para abrir carpeta
    def open_pak_folder(self):
        os.startfile(self.pak_folder)

    def load_servers(self):
        """Carga la lista de servidores guardados"""
        try:
            if os.path.exists(SERVERS_FILE):
                with open(SERVERS_FILE, 'r') as f:
                    self.servers = json.load(f)
                self.update_server_list()
        except Exception as e:
            logging.error(f"Error al cargar servidores: {str(e)}")

    def save_server(self):
        """Guarda el servidor actual en la lista"""
        try:
            ip = self.ip_entry.get().strip()
            if not ip or ':' not in ip:
                messagebox.showerror("Error", "IP inválida")
                return
            
            # Inicializar el archivo de servidores si no existe
            if not hasattr(self, 'servers'):
                self.servers = {}
            
            # Guardar servidor con timestamp
            self.servers[ip] = {
                "last_used": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Guardar en archivo
            with open(SERVERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.servers, f, indent=4, ensure_ascii=False)
            
            # Actualizar lista
            self.update_server_list()
            messagebox.showinfo("Éxito", f"Servidor {ip} guardado correctamente")
            
        except Exception as e:
            error_msg = f"Error al guardar servidor: {str(e)}"
            logging.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def on_server_select(self, event):
        """Maneja la selección de un servidor de la lista"""
        try:
            selection = self.server_listbox.curselection()
            if selection:
                ip = list(self.servers.keys())[selection[0]]
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, ip)
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
                self.server_listbox.insert(tk.END, ip)
        except Exception as e:
            logging.error(f"Error al actualizar lista de servidores: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = IsleLauncher(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error fatal en la aplicación: {str(e)}")
        messagebox.showerror("Error Fatal", f"La aplicación no pudo iniciarse: {str(e)}")