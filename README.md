# Control Interface Project

Este proyecto está diseñado con Kivy, una librería Python para desarrollar aplicaciones con interfaces gráficas. Se centra en un sistema de control con múltiples modos (Manual, Semi, Auto) y una serie de botones para manejar el tiempo de viaje, el tiempo de espera y activar funciones especiales como un "buzzer" y "comer fichas". 

## Descripción del Proyecto

Este sistema permite gestionar diferentes modos de operación (manual, semi, automático) mediante un conjunto de botones. Además, proporciona control sobre el tiempo de viaje y el tiempo de espera, y permite activar una serie de botones especiales como el buzzer. La interfaz gráfica está construida en Kivy utilizando el lenguaje de diseño KV para definir el layout.

### Funcionalidades:
1. **Modos de Operación**:
   - **Manual**: Operación controlada manualmente por el usuario.
   - **Semi**: Semi-automatizado con intervención del usuario.
   - **Auto**: Completamente automatizado.

2. **Control de Tiempos**:
   - Incremento y decremento del tiempo de viaje y el tiempo de espera mediante los botones "+" y "-".

3. **Botones Especiales**:
   - Activar "Descarga" con el botón "ACTIVAR DESCARGA".
   - "Comer Fichas" y activar el buzzer.

4. **Estado del Sistema**:
   - Los botones de "START", "PAUSE" y "STOP" permiten controlar el estado del sistema.

### Estructura de Archivos:
1. **main.py**: Contiene el código Python que maneja la lógica de la aplicación.
2. **interface.kv**: Define el diseño y la apariencia de la interfaz de usuario utilizando el lenguaje KV de Kivy.

---

## Requisitos

Para ejecutar este proyecto, necesitas tener instaladas las siguientes dependencias:

- **Python** 3.x
- **Kivy** 2.x

## actualizar sistema abrir consola ssh:

```bash
sudo raspi-config:
   interface_options: VNC/enable (k0)
sudo apt-get update
sudo apt-get upgrade
```
## crear entorno virtual:

```bash
   #crear entorno virtual
   python3 -m venv env
   #entrar a entorno
   source env/bin/activate
   python3 -m pip install --upgrade pip setuptools virtualenv
   pip install kivy
   sudo apt-get install libgl1-mesa-glx libgles2-mesa libegl1-mesa libmtdev1
   pip install gpiozero

   sudo apt install python3-pip python3-dev -y
   sudo apt install python3-rpi.gpio python3-pigpio python3-gpiozero -y
   pip install --upgrade pyinstaller
   pyinstaller --version
   sudo pigpiod
```
## cambiar el config.init de kivy:

```bash
cd sudo nano /home/pi/.kivy/config.ini 

```
reemplazar por  /kivy/config.ini

## ocultar arranque:
```bash
   sudo nano /boot/firmware/cmdline.txt
   console=serial0,115200 console=tty3 root=PARTUUID=xxxxxx-xx rootfstype=ext4 fsck.repair=yes rootwait loglevel=3 consoleblank=0 plymouth.enable=0
```

## crear servicio:

```bash
sudo nano /etc/systemd/system/game.service

[Unit]
Description=Game_App
After=pigpiod.service multi-user.target graphical.target
Wants=graphical.target
Requires=pigpiod.service

[Service]
User=pi
ExecStart=/home/pi/env/src/game/dist/main
WorkingDirectory=/home/pi/
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
Environment=XAUTHORITY=/home/pi/.Xauthority
Restart=always
RestartSec=1

[Install]
WantedBy=graphical.target

```
## comandos de servicio de auto ejecucion y encendido automatico

```bash
sudo systemctl daemon-reload
sudo systemctl enable game.service
sudo systemctl start game.service
journalctl -u game.service --no-pager --lines=50
sudo systemctl status game.service
sudo systemctl stop game.service
sudo systemctl disabled game.service
```

## crear ejecutable
iniciar el entorno virtual, pararse en la carpeta del main

```bash
   pyinstaller --onefile  --windowed --add-data="game.kv:." --add-data="hardware.py:." game.py
   or 
   pyinstaller main.spec

```

## calibrando el tactil
```bash
sudo nano /boot/firmware/config.txt
   display_rotate=0
   hdmi_force_hotplug=1
   hdmi_mode=87
   hdmi_cvt=1024 600 60 3 0 0 0

sudo nano /usr/share/X11/xorg.conf.d/40-libinput.conf 
   Option "CalibrationMatrix" "1 0 0 0 1 0 0 0 1"
   
sudo cp /usr/share/X11/xorg.conf.d/40-libinput.conf /etc/X11/xorg.conf.d/

sudo apt-get update
sudo apt-get install xinput xinput-calibrator

xinput list
xinput_calibrator --device "xwayland-touch:14"
sudo nanod /etc/X11/xorg.conf.d/99-calibration.conf         
   Section "InputClass"
      Identifier      "calibration"
      MatchProduct    "xwayland-touch:14"
      Option  "MinX"  "443"
      Option  "MaxX"  "65764"
      Option  "MinY"  "437"
      Option  "MaxY"  "63787"
      Option  "SwapXY"        "0" # unless it was already set to 1
      Option  "InvertX"       "0"  # unless it was already set
      Option  "InvertY"       "0"  # unless it was already set
   EndSection
```