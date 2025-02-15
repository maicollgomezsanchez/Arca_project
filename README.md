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
    sudo apt install python3-gpiozero
    python3 -m venv env
    #entrar a entorno
    source env/bin/activate
    pip3 install kivy
    pip3 install gpiozero
    pip3 install lgpio
    apt install pigpio
    pip install RPi.GPIO pigpio
    pip3 install --upgrade pyinstaller
    pyinstaller --version
    mkdir game
    mkdir src

   sudo systemctl start pigpiod
   sudo systemctl enable pigpiod
   sudo systemctl status pigpiod


```

## ocultar arranque:
```bash
    pass: R4spb3rr7
    sudo nano /boot/firmware/cmdline.txt:
        loglevel=1 quiet splash vt.global_cursor_default=0

   sudo apt install plymouth plymouth-themes
   sudo plymouth-set-default-theme details
   sudo update-initramfs -u

   sudo nano /etc/lightdm/lightdm-autologin.conf:
        autologin-user = pi
        autologin-user-timeout = 0
   
    sudo reboot 
```


## crear aplicacion

```bash
   sudo apt install python3-pip python3-dev -y
   sudo apt install python3-rpi.gpio python3-pigpio python3-gpiozero -y

   pyinstaller --onefile  --windowed --add-data="vista.kv:." main.py

   pyinstaller --onefile  hmi.py

```
luego mover el ejecutable a:

```bash
cd /home/pi/kivy_venv/src/game/dist/
```

## crear autoejecutable:

```bash
sudo nano /etc/systemd/system/game.service

[Unit]
Description=Game_App
After=multi-user.target
Wants=graphical.target

[Service]
ExecStart=/home/pi/kivy_venv/src/game/dist/main
WorkingDirectory=/home/pi/kivy_venv/src/game
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/1000
Restart=always
User=pi
Group=pi

ExecStartPre=/bin/sh -c 'chmod a+rw /dev/gpiomem'
ExecStartPre=/bin/sh -c 'chmod a+rw /sys/class/gpio/*'
ExecStartPre=/bin/sh -c 'chmod a+rw /dev/mem'

ExecStartPre=/usr/bin/systemctl start pigpiod
ExecStartPre=/bin/sleep 5

[Install]
WantedBy=graphical.target
```
## comandos de servicio de auto ejecucion y encendido automatico

```bash
sudo systemctl daemon-reload
sudo systemctl enable game.service
sudo systemctl start game.service

cat /etc/systemd/system/game.service
DISPLAY=:0 /home/pi/kivy_venv/src/game/dist/main
journalctl -u game.service --no-pager --lines=50

sudo systemctl status game.service
sudo systemctl restart game.service

sudo systemctl disable game.service
```