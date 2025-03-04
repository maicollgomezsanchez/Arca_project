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
   interface_options: VNC/enable
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


## crear ejecutable

```bash
   pyinstaller --onefile  --windowed --add-data="main.kv:." main.py
   or 
   pyinstaller main.spec


```
luego mover el ejecutable a:

```bash
cd /home/pi/env/src/game/dist/
```

## crear servicio:

```bash
sudo nano /etc/systemd/system/game.service

[Unit]
Description=Game_App
After=multi-user.target
Wants=graphical.target

[Service]
User=pi
ExecStart=/bin/bash -c "echo 'Iniciando el script' > /home/pi/log/logs.txt && source /home/pi/env/bin/activate && python /home/pi/env/src/game/main.py >> /home/pi/log/logs.txt 2>&1"
WorkingDirectory=/home/pi/
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/1000
StandardOutput=append:/home/pi/log/logs.txt
StandardError=append:/home/pi/log/logs.txt
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

cat /etc/systemd/system/game.service
DISPLAY=:0 /home/pi/env/src/game/dist/main
journalctl -u game.service --no-pager --lines=50

sudo systemctl status game.service
sudo systemctl stop game.service
sudo systemctl disabled game.service
```

configuara el kivi init