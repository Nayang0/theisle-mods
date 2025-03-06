import os
import hashlib
import json

# URLs de los mods en Google Drive
DRIVE_URLS = {
    'TheIsle-Zzz_Yutty.pak': 'https://drive.google.com/uc?export=download&id=1o4p0B4NFdRUReQh5Z4wYPx457SJne_oE',
    'TheIsle-Zzz_Yutty.sig': 'https://drive.google.com/uc?export=download&id=1wbeqgcmNn7gIR8BCRiBbz62rV1Typjbq'
}

def generate_hash(filepath):
    """Genera el hash SHA256 de un archivo"""
    try:
        print(f"Calculando hash para: {filepath}")
        file_size = os.path.getsize(filepath)
        print(f"Tamaño del archivo: {file_size} bytes")
        
        with open(filepath, 'rb') as f:
            # Leer todo el archivo en memoria
            content = f.read()
            # Calcular hash
            file_hash = hashlib.sha256(content).hexdigest()
            print(f"Hash calculado: {file_hash}")
            return file_hash
    except Exception as e:
        print(f"Error al procesar {filepath}: {str(e)}")
        return None

def generate_mod_list(directory):
    """Genera el archivo mods.txt con los hashes de los archivos"""
    with open('mods.txt', 'w') as f:
        f.write("# filename hash download_url\n")
        
        for filename in os.listdir(directory):
            if filename.endswith(('.pak', '.sig')):
                filepath = os.path.join(directory, filename)
                file_hash = generate_hash(filepath)
                if file_hash:
                    # Usar URL de Google Drive si está disponible
                    download_url = DRIVE_URLS.get(filename, "URL_NO_CONFIGURADA")
                    f.write(f"{filename} {file_hash} {download_url}\n")
                    print(f"Procesado: {filename}")
                    print(f"Hash: {file_hash}")
                    print(f"URL: {download_url}\n")

if __name__ == "__main__":
    mods_directory = os.path.join(os.path.dirname(__file__), 'mods')
    if not os.path.exists(mods_directory):
        os.makedirs(mods_directory)
        print("Carpeta 'mods' creada")
    generate_mod_list(mods_directory)