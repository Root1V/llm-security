"""Script para ejecutar el servidor en modo desarrollo"""
import os
import sys
from pathlib import Path
import uvicorn


def main():
    """Ejecuta el servidor en modo desarrollo con recarga automática"""
    # Asegurar que estemos en el directorio del proyecto
    # El script se encuentra en scripts/, el proyecto está en el padre
    project_root = Path(__file__).parent.parent.absolute()
    
    # Agregar el directorio del proyecto al Python path
    sys.path.insert(0, str(project_root))
    
    # Cambiar al directorio del proyecto
    os.chdir(project_root)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
    )


if __name__ == "__main__":
    main()
