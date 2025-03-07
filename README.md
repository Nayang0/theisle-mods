# Lanzador de The Isle Legacy

Lanzador moderno para The Isle Legacy con detección e instalación automática de mods.

## Características
- Detección automática de mods del servidor a través del protocolo Steam A2S_INFO
- Integración con GitHub para descargas de mods
- Sistema de creación de mods
- Detección automática de rutas de juego
- Compatibilidad con varios creadores
- Gestión de servidores

## Requisitos
- Sistema operativo Windows
- The Isle Legacy instalado

## Instalación
1. Descarga la última versión
2. Ejecuta `TheIsle Legacy Launcher.exe`
3. Configura las rutas de tu juego
4. ¡Empieza a jugar!

## Para propietarios de servidores
Agrega `[github=username/repo]` al nombre de tu servidor en Game.ini para la detección automática de mods.
Ejemplo:
```ini
ServerName=My Server [github=Nayang0/theisle-mods]
```

## Para desarrolladores
### Creación desde el código fuente
1. Clonar el repositorio
2. Instalar los requisitos de Python: `pip install -r requirements.txt`
3. Crear el ejecutable: `pyinstaller launcher.spec`