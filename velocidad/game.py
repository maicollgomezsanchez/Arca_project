from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup


import time, threading
import os
import stat
import shutil
import hardware

import platform
SO = platform.system()

if SO == "Windows":
    try:
        import win32file
    except ImportError:
        win32file = None
else:
    win32file = None


PERIMETRO = 35 # en metros
TIMEOUT = 30 # segundos sin pulsos para cerrar archivo

def window_setup():
    Window.borderless = False
    Window.fullscreen = True
    Window.show_cursor = False
    Window.release_all_keyboards()

def export_to_usb(source_file, usb_drive):
    try:
        destination = os.path.join(usb_drive, os.path.basename(source_file))
        shutil.copy2(source_file, destination)
    except Exception as e:
        hardware.log.warning(f"Error exportando archivo: {e}")

def get_usb_drives():
    if SO == "Windows":
        return get_usb_drives_windows()
    else:
        return get_usb_drives_linux()

def get_usb_drives_windows():
    if win32file is None:
        return []

    drives = []
    bitmask = win32file.GetLogicalDrives()
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if bitmask & 1:
            drive = f"{letter}:\\"
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                drives.append(drive)
        bitmask >>= 1
    return drives


def get_usb_drives_linux():
    drives = []
    media_path = "/media/pi"

    if not os.path.exists(media_path):
        return drives

    for item in os.listdir(media_path):
        full_path = os.path.join(media_path, item)
        if os.path.ismount(full_path):
            drives.append(full_path)

    return drives


class MainScreen(Screen):
    speed = NumericProperty(0)
    active_file = StringProperty("")
    
  #variables globales
    def init_vars(self):
        self.RPM_sensor = False
        self.popup = None

        # Control de archivo
        self.log_enabled = False
        self.log_filename = None
        self.last_pulse_time = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.init_vars()
        self.thread_speed = threading.Thread(
            target=self.read_speed,
            args=(self.read_RPM, PERIMETRO),
            daemon=True
        )
        self.thread_speed.start()
        #enlazar sensor con 
        hardware.input_sensor.when_pressed = self.on_sensor
        hardware.input_sensor.when_released  = self.off_sensor

    def deinit(self):
        self.running = False
        try:
            self.thread_speed.join(timeout=1)
            hardware.log.info("Hilos detenidos correctamente")
        except Exception as e:
            hardware.log.error(f"Error al detener los hilos: {e}")
        finally:
            if self.log_enabled: self.close_and_save_file()
            hardware.log.info("Pines cerrados correctamente")
            hardware.close_all_pins()

    # hilo 
    def read_speed(self, get_RPM, _P_mts):
        self._last = None
        hardware.log.info("inicia sensor de velocidad")
        while self.running:
            # Esperar flanco de subida
            while not get_RPM():
                if not self.running:
                    if self.log_enabled: 
                        self.close_and_save_file()
                    return
                now_ = time.time()
                # Cerrar archivo si pasan timeout sin pulsos o un solo pulso
                if self.last_pulse_time:
                    if (now_ - self.last_pulse_time) >= TIMEOUT:
                        self.last_pulse_time = None
                        if self.log_enabled:
                            hardware.log.info("cerrando por timeout")
                        self.close_and_save_file()
                time.sleep(0.001)
            #pulso detectado
            _now = time.time()
            self.last_pulse_time = _now

            if self._last is not None:
                _dt = _now - self._last

                if _dt > 0:
                    _m_s = _P_mts / _dt
                    _km_h = _m_s * 3.6

                    Clock.schedule_once( lambda _: self.export_values(_km_h))
                    self.save_events(_km_h, _dt)

            self._last = _now

            while get_RPM():
                if not self.running:
                    if self.log_enabled: 
                        self.close_and_save_file()
                    return
                time.sleep(0.001)

    def read_RPM(self):
        return self.RPM_sensor
        
    def on_sensor(self):
        self.RPM_sensor = True
    
    def off_sensor(self):
        self.RPM_sensor = False

 
# log events
    def export_values (self, _speed):
        self.speed = int(_speed)
    
    def save_events(self, velocidad, dt):
        if not self.log_enabled:
            dt_name = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            self.log_filename = f"Evento_{dt_name}.txt"
            self.log_enabled = True
            hardware.log.info(f"Nuevo archivo creado: {self.log_filename}")
            self.active_file = self.log_filename

        self.last_pulse_time = time.time()
        dt_name = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        linea = f"Fecha y Hora = {dt_name}, Velocidad = {int(velocidad)} km/h, Tiempo = {dt:.2f} s\n"

        try:
            with open(self.log_filename, "a", buffering=1) as f:
                f.write(linea)
        except Exception as e:
            hardware.log.error("Error escribiendo archivo:", e)
    
    def close_and_save_file(self):
        self._last = None
        self.speed = 0
        if not self.log_enabled or not self.log_filename: return

        try:
            os.chmod(self.log_filename, stat.S_IREAD)
            hardware.log.info(f"Archivo {self.log_filename} cerrado y puesto en solo lectura.")
            self.active_file = ""
        except Exception as e:
            hardware.log.error("Error al cerrar archivo:", e)

        self.log_enabled = False
        self.log_filename = None

# nuevas pantallas


class ReusablePopup(Popup):
    title_text = StringProperty("")
    message = StringProperty("")
    on_confirm = ObjectProperty(None)
    confirm_mode = BooleanProperty(False)

class FileListScreen(Screen):
    def show_popup(self, title, message, on_confirm=None):
        def _open(dt):
            popup = Factory.ReusablePopup()
            popup.title_text = title
            popup.message = message
            popup.confirm_mode = on_confirm is not None

            # Si el popup tiene un botón OK, le asignamos la acción
            if on_confirm:
                popup.on_confirm = on_confirm

            popup.open()

        Clock.schedule_once(_open, 0)

        
    def on_pre_enter(self):
        files = [f for f in os.listdir(".") if f.startswith("Evento_") and f.endswith(".txt")]

        # Limpiar lista
        self.ids.file_list.clear_widgets()

        # Crear botones por archivo
        for fname in files:
            btn = Button(
                text=fname,
                size_hint_y=None,
                height=40,
                on_release=lambda b, f=fname: self.open_file(f)
            )
            self.ids.file_list.add_widget(btn)

    def open_file(self, filename):
        viewer = self.manager.get_screen("file_viewer")
        viewer.load_file(filename)
        self.manager.current = "file_viewer"
        
    def exportar_todos_usb(self):
        usb_list = get_usb_drives()
        hardware.log.warning(f"USB detectados: {usb_list}")
        if not usb_list:
            hardware.log.warning("No hay USB conectado")
            self.show_popup("AVISO", "NO HAY USB CONECTADO")
            return

        usb = usb_list[0]
        files = [f for f in os.listdir(".") if f.endswith(".txt")]

        for f in files:
            export_to_usb(f, usb)
        
        if files:
            self.show_popup("AVISO", "ARCHIVOS EXPORTADOS")
    
    def borrar_archivos(self):
        files = [f for f in os.listdir(".") if f.startswith("Evento_") and f.endswith(".txt")]

        if not files:
            self.show_popup("AVISO", "SIN EVENTOS")
            return

        # Mostrar popup de confirmación
        self.show_popup(
            "AVISO",
            "¿DESEA ELIMINAR TODOS LOS EVENTOS?",
            on_confirm=lambda: self._borrar_archivos_confirmado(files)
        )

            
    def _borrar_archivos_confirmado(self, files):
        for fname in files:
            try:
                os.chmod(fname, stat.S_IWRITE)
                os.remove(fname)

            except PermissionError:
                self.show_popup("ERROR", f"ARCHIVO PROTEGIDO: {fname}")
                return

            except Exception as e:
                self.show_popup("ERROR", f"NO SE HA ELIMINADO: {fname}")
                return

        # Actualizar lista visual
        self.ids.file_list.clear_widgets()
        self.show_popup("AVISO", "EVENTOS ELIMINADOS")


class FileViewerScreen(Screen):
    content = StringProperty("")
    filename_open = StringProperty("")

    def load_file(self, filename):
        try:
            with open(filename, "r") as f:
                self.content = f.read()
            self.filename_open = filename
        except Exception as e:
            self.content = f"Error al abrir archivo:\n{e}"

class mainApp(App):
    def build(self):
        window_setup()
        return Builder.load_file("game.kv")

    def on_stop(self):
        main_screen = self.root.get_screen("main")
        main_screen.deinit()

if __name__ == "__main__":
    try:
        #Builder.load_file('speed.kv')
        mainApp().run()
    except Exception as e:
        hardware.log.error(f"error de excepcion {e}")
    except KeyboardInterrupt:
        hardware.log.error("keyboard exit")
    finally:
        hardware.close_all_pins()
