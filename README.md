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
pi 
deshabiitar volumenes extraibles pop up:
To get rid of the popup message:
Open File-manager
[Edit] --> [Preferences] --> [Volume Management]

Remove tick from:
[ ] Show available options for...........


To get rid of desktop icon:
Right click on screen --> [Desktop Preferences]

Remove tick from:
[ ] Mounted Disks


con la instalacion de bulleye:

raspy con bulleye


python version 3.9.2
sudo apt install python3-kivy



creando servicio:
```bash

sudo nano /etc/systemd/system/game.service

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

sudo systemctl daemon-reload
sudo systemctl enable game.service
sudo systemctl start game.service
```

ocultar arranque:
```bash
   sudo nano /boot/cmdline.txt

   console=serial0,115200 console=tty3 root=/dev/mmcblk0p2 rootfstype=ext4 fsck.repair=yes rootwait loglevel=3 consoleblank=0 plymouth.enable=0
```


cambiar el config.init de kivy:

```bash
cd sudo nano /home/pi/.kivy/config.ini 

```

instalando gpiozero

```bash
   sudo apt install python3-gpiozero
   sudo apt install python-gpiozero
```