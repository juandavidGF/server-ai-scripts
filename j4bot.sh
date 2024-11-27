#!/bin/bash

# Verificar si el sistema operativo es Linux
if [[ "$(uname)" == "Linux" ]]; then
    echo "El sistema operativo es Linux. Continuando con la instalación..."

    # Actualizar el sistema
    echo "Actualizando el sistema..."
    sudo apt update && sudo apt upgrade -y

    # Instalar Node.js (versión 20.x)
    echo "Instalando Node.js y npm..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs

    # Verificar instalación de Node.js y npm
    echo "Verificando versiones de Node.js y npm..."
    node -v
    npm -v

    # Instalar TypeScript y ts-node
    echo "Instalando TypeScript y ts-node..."
    sudo npm install -g typescript ts-node

    # Verificar instalación de TypeScript y ts-node
    echo "Verificando instalación de TypeScript y ts-node..."
    tsc -v
    ts-node -v

    # Instalar pm2
    echo "Instalando pm2..."
    sudo npm install -g pm2

    # Verificar instalación de pm2
    echo "Verificando instalación de pm2..."
    pm2 -v

    echo "Instalación completada exitosamente."

else
    echo "Este script solo es compatible con sistemas operativos Linux. Aborting..."
    exit 1
fi

