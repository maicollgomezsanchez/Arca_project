#!/bin/bash

set -e

echo "Usuario actual: $(whoami)"

echo "Actualizando sistema..."
sudo apt update -y
sudo apt upgrade -y

echo "Instalando Kivy..."
sudo apt install -y python3-kivy

echo "Configurando arranque silencioso..."
CMDLINE_FILE="/boot/cmdline.txt"

# Backup previo
sudo cp $CMDLINE_FILE ${CMDLINE_FILE}.bak

# Sobrescribir configuración
sudo bash -c "cat > $CMDLINE_FILE" <<EOF
console=serial0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 fsck.repair=yes rootwait loglevel=3 consoleblank=0 plymouth.enable=0 quiet vt.global_cursor_default=0 logo.nologo
EOF

echo "Creando estructura manual de Kivy..."

mkdir -p /home/pi/.kivy
mkdir -p /home/pi/.kivy/logs
mkdir -p /home/pi/.kivy/mods
mkdir -p /home/pi/.kivy/icon

echo "Copiando config.ini..."
cp -f /home/pi/Game/config.ini /home/pi/.kivy/config.ini

echo "Asegurando permisos correctos..."
sudo chown -R pi:pi /home/pi/.kivy

echo "Creando servicio systemd..."
SERVICE_FILE="/etc/systemd/system/game.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Game_App
After=graphical.target

[Service]
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
WorkingDirectory=/home/pi/Game

ExecStartPre=/bin/sleep 5
ExecStartPre=/bin/mkdir -p /home/pi/.kivy
ExecStartPre=/bin/cp -f /home/pi/Game/config.ini /home/pi/.kivy/config.ini

ExecStart=/usr/bin/python3 /home/pi/Game/game.py

Restart=always
RestartSec=1

[Install]
WantedBy=graphical.target
EOF

echo "Recargando systemd..."
sudo systemctl daemon-reload

echo "Habilitando servicio..."
sudo systemctl enable game.service

echo "Iniciando servicio..."
sudo systemctl start game.service

echo "Proceso finalizado correctamente."
echo "Reinicia el sistema con: sudo reboot"