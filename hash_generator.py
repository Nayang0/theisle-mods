import os
import hashlib

def generate_hash(filepath):
    """Genera el hash SHA256 de un archivo"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        print(f"Error al procesar {filepath}: {str(e)}")
        return None

def generate_mod_list(directory):
    """Genera el archivo mods.txt con los hashes de los archivos .pak y .sig"""
    with open('mods.txt', 'w') as f:
        f.write("# filename hash download_url\n")
        
        for filename in os.listdir(directory):
            if filename.endswith(('.pak', '.sig')):
                filepath = os.path.join(directory, filename)
                file_hash = generate_hash(filepath)
                if file_hash:
                    # Por ahora usamos una URL de ejemplo
                    download_url = "https://example.com/" + filename
                    f.write(f"{filename} {file_hash} {download_url}\n")

if __name__ == "__main__":
    # Usar la carpeta mods por defecto
    default_mods_directory = os.path.join(os.path.dirname(__file__), 'mods')
    
    # Crear la carpeta mods si no existe
    if not os.path.exists(default_mods_directory):
        os.makedirs(default_mods_directory)
        print(f"Carpeta 'mods' creada en: {default_mods_directory}")
        print("Por favor, coloca tus archivos .pak y .sig en esta carpeta")
        exit()

    # Verificar si hay archivos en la carpeta
    if not any(f.endswith(('.pak', '.sig')) for f in os.listdir(default_mods_directory)):
        print("No se encontraron archivos .pak o .sig en la carpeta mods")
        print(f"Por favor, coloca tus archivos en: {default_mods_directory}")
        exit()

    # Generar hashes
    generate_mod_list(default_mods_directory)
    print(f"Archivo mods.txt generado exitosamente!")
    print("Los hashes han sido calculados para todos los archivos .pak y .sig")