#!/bin/bash

set -u

echo "======================================="
echo " CONFIGURACION INICIAL DE GAME APP"
echo "======================================="

echo ""
echo "Comprobando conexión a Internet..."

if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then

    echo "Internet disponible."

    echo "Actualizando sistema..."
    sudo apt update -y || echo "No se pudo ejecutar apt update"

    echo "Actualizando paquetes..."
    sudo apt upgrade -y || echo "No se pudo ejecutar apt upgrade"

    echo "Comprobando instalación de Kivy..."

    if ! dpkg -s python3-kivy >/dev/null 2>&1; then
        echo "Instalando Kivy..."
        sudo apt install -y python3-kivy || echo "No se pudo instalar Kivy"
    else
        echo "Kivy ya instalado."
    fi

else

    echo "Sin conexión a Internet."
    echo "Se omite actualización e instalación de paquetes."

fi

echo ""
echo "Configurando arranque silencioso..."

CMDLINE_FILE="/boot/cmdline.txt"

if [ -f "$CMDLINE_FILE" ]; then

    sudo cp "$CMDLINE_FILE" "${CMDLINE_FILE}.bak"

    sudo bash -c "cat > $CMDLINE_FILE" <<EOF
console=serial0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 fsck.repair=yes rootwait loglevel=3 consoleblank=0 plymouth.enable=0 quiet vt.global_cursor_default=0 logo.nologo
EOF

    echo "cmdline.txt actualizado."

else

    echo "No existe $CMDLINE_FILE"

fi

CONFIG_FILE="/boot/config.txt"

if [ -f "$CONFIG_FILE" ]; then

    sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"

    # Limpiar configuraciones previas
    sudo sed -i '/^gpio=18=op,/d' "$CONFIG_FILE"
    sudo sed -i '/^gpio=23=op,/d' "$CONFIG_FILE"
    sudo sed -i '/^gpio=24=op,/d' "$CONFIG_FILE"
    sudo sed -i '/^gpio=25=op,/d' "$CONFIG_FILE"
    sudo sed -i '/^gpio=12=op,/d' "$CONFIG_FILE"
    sudo sed -i '/^gpio=17=ip/d' "$CONFIG_FILE"
    sudo sed -i '/^gpio=27=ip/d' "$CONFIG_FILE"

    sudo tee -a "$CONFIG_FILE" >/dev/null <<EOF

# Mantener señal HDMI aunque no haya monitor
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 30

# GPIO salidas LOW al arrancar
gpio=18=op,dl
gpio=23=op,dl
gpio=24=op,dl
gpio=25=op,dl
gpio=12=op,dl

# Entradas
gpio=17=ip
gpio=27=ip

EOF

    echo "config.txt actualizado."

else

    echo "No existe $CONFIG_FILE"

fi

echo ""
echo "Creando estructura manual de Kivy..."

mkdir -p /home/pi/.kivy
mkdir -p /home/pi/.kivy/logs
mkdir -p /home/pi/.kivy/mods
mkdir -p /home/pi/.kivy/icon

echo "Directorios creados."

echo ""
echo "Copiando config.ini..."

if [ -f /home/pi/Game/config.ini ]; then

    cp -f /home/pi/Game/config.ini /home/pi/.kivy/config.ini
    echo "config.ini copiado."

else

    echo "ADVERTENCIA: /home/pi/Game/config.ini no encontrado."

fi

echo ""
echo "Ajustando permisos..."

sudo chown -R pi:pi /home/pi/.kivy || echo "Error asignando permisos"

echo ""
echo "Comprobando aplicación..."

if [ ! -f /home/pi/Game/game.py ]; then
    echo "ERROR CRITICO: No existe /home/pi/Game/game.py"
    exit 1
fi

echo "game.py encontrado."

echo ""
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

ExecStartPre=/bin/sleep 3
ExecStart=/usr/bin/python3 /home/pi/Game/game.py

Restart=always
RestartSec=1

[Install]
WantedBy=graphical.target
EOF

echo "Servicio creado."

echo ""
echo "Recargando systemd..."
sudo systemctl daemon-reload || echo "Error en daemon-reload"

echo "Habilitando servicio..."
sudo systemctl enable game.service || echo "Error habilitando servicio"

echo "Iniciando servicio..."
sudo systemctl start game.service || echo "Error iniciando servicio"

echo ""
echo "======================================="
echo " PROCESO FINALIZADO"
echo "======================================="
echo ""
read -p "Presiona ENTER para cerrar la ventana..."
