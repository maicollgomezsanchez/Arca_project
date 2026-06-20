#!/bin/bash

echo "========== INSTALADOR GAME =========="

# 1. Actualizar sistema
echo ">>> Actualizando sistema..."
sudo apt update -y

# 2. Instalar Kivy
echo ">>> Instalando python3-kivy..."
sudo apt install -y python3-kivy

# 3. Ocultar logs de arranque
echo ">>> Configurando arranque oculto..."
sudo sed -i '1c\console=serial0,115200 console=tty3 root=/dev/mmcblk0p2 rootfstype=ext4 fsck.repair=yes rootwait loglevel=3 consoleblank=0 plymouth.enable=0' /boot/cmdline.txt

# 4. Crear carpeta destino
echo ">>> Creando carpeta destino..."
sudo mkdir -p /home/pi/Game

# 5. Copiar todo EXCEPTO el instalador
echo ">>> Copiando archivos del juego..."
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

for item in "$SRC_DIR"/*; do
    name=$(basename "$item")
    
    if [ "$name" != "install_game.sh" ]; then
        cp -r "$item" /home/pi/Game/
    fi
done

# 6. Permisos
echo ">>> Ajustando permisos..."
sudo chown -R pi:pi /home/pi/Game

# 7. Crear servicio systemd
echo ">>> Creando servicio..."
sudo bash -c 'cat > /etc/systemd/system/game.service <<EOF
[Unit]
Description=Game_App
After=multi-user.target graphical.target
Wants=graphical.target

[Service]
User=pi
WorkingDirectory=/home/pi/Game
ExecStart=/usr/bin/python3 /home/pi/Game/game.py

Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
Environment=XAUTHORITY=/home/pi/.Xauthority

Restart=always
RestartSec=1

[Install]
WantedBy=graphical.target
EOF'

# 8. Activar servicio
echo ">>> Activando servicio..."
sudo systemctl daemon-reload
sudo systemctl enable game.service
sudo systemctl start game.service

echo "========== TODO LISTO =========="
echo ">>> Reinicia con: sudo reboot"