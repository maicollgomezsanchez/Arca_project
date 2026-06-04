from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.factory import Factory

import time, threading
import logging
import os
import stat
import shutil

import platform
SO = platform.system()

if SO == "Windows":
    try:
        import win32file
    except ImportError:
        win32file = None
else:
    win32file = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

PERIMETRO = 35 # en metros

def window_setup():
    Window.borderless = False
    Window.fullscreen = False
    Window.show_cursor = True
    Window.release_all_keyboards()

def export_to_usb(source_file, usb_drive):
    try:
        destination = os.path.join(usb_drive, os.path.basename(source_file))
        shutil.copy2(source_file, destination)
    except Exception as e:
        log.warning(f"Error exportando archivo: {e}")

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
    base = f"/media/{os.getlogin()}/"
    if not os.path.exists(base):
        return []

    drives = []
    for d in os.listdir(base):
        path = os.path.join(base, d)
        if os.path.ismount(path):
            drives.append(path)
    return drives

class MainScreen(Screen):
    speed = NumericProperty(0)
    active_file = StringProperty("")
    
  #variables globales
    def init_vars(self):
        #self.counter_pulse = None
        self.RPM_sensor = False
        self.popup_enabled = False
        self.popup = None
        self.buttons_name = ["stop_button"]

        # Control de archivo
        self.log_enabled = False
        self.log_filename = None
        self.last_pulse_time = None
        self.log_timeout = 60  # segundos sin pulsos para cerrar archivo


    # funciones HMI
    def init_hmi_buts(self):
        for ids in self.buttons_name:
            setattr(self, ids, self.ids[ids])

    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.init_vars()
        #self.init_hmi_buts()
        self.thread_speed = threading.Thread(target=self.read_speed, args=(self.read_RPM, PERIMETRO), daemon=True)
        self.thread_speed.start()

    def deinit(self):
        self.running = False
        try:
            self.thread_speed.join(timeout=1)
            log.info("Hilos detenidos correctamente")
        except Exception as e:
            log.error(f"Error al detener los hilos: {e}")
        finally:
            if self.log_enabled: self.close_and_save_file()
            log.info("Pines cerrados correctamente")

    # hilo 
    def read_speed(self, get_RPM, _P_mts):
        self._last = None
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
                    if (now_ - self.last_pulse_time) >= self.log_timeout:
                        self.last_pulse_time = None
                        if not self.log_enabled: 
                            log.warning("un solo pulso no contar")
                        else:
                            log.info("cerrando por timeout")
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

            # Esperar a que el relé vuelva a abrirse
            while get_RPM():
                if not self.running:
                    if self.log_enabled: 
                        self.close_and_save_file()
                    return
                time.sleep(0.001)

    def read_RPM(self):
        return self.RPM_sensor
    
    def simular_pulso(self):
        self.RPM_sensor = True
        time.sleep(0.01)
        self.RPM_sensor = False
        

# log events
    def export_values (self, _speed):
        self.speed = int(_speed)
    
    def save_events(self, velocidad, dt):
        if not self.log_enabled:
            dt_name = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            self.log_filename = f"Evento_{dt_name}.txt"
            self.log_enabled = True
            log.info(f"Nuevo archivo creado: {self.log_filename}")
            self.active_file = self.log_filename

        self.last_pulse_time = time.time()
        dt_name = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        linea = f"Fecha y Hora = {dt_name}, Velocidad = {int(velocidad)} km/h, Duración = {dt:.2f} s\n"

        try:
            with open(self.log_filename, "a", buffering=1) as f:
                f.write(linea)
        except Exception as e:
            log.error("Error escribiendo archivo:", e)
    
    def close_and_save_file(self):
        self._last = None
        self.speed = 0
        if not self.log_enabled or not self.log_filename: return

        try:
            os.chmod(self.log_filename, stat.S_IREAD)
            log.info(f"Archivo {self.log_filename} cerrado y puesto en solo lectura.")
            self.active_file = ""
        except Exception as e:
            log.error("Error al cerrar archivo:", e)

        self.log_enabled = False
        self.log_filename = None



# fucniones tactiles
    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if not self.collide_point(*touch.pos):
                self.on_touch_up(touch)
                touch.ungrab(self)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        return super().on_touch_up(touch)

    def on_touch_down(self, touch):
        for widget_id in self.buttons_name:
            btn = self.ids[widget_id]
            if btn.collide_point(*touch.pos):
                touch.grab(self)

                if widget_id == "stop_button":
                    log.info("press button")
                    self.simular_pulso()
                    return True  # ya manejado

        # Si no fue el stop_button, deja que los hijos (incluido "Ver archivos") procesen el toque
        return super().on_touch_down(touch)

# nuevas pantallas
class FileListScreen(Screen):
    def show_popup(self, title, message):
        popup = Factory.ReusablePopup()
        popup.title_text = title
        popup.message = message
        popup.open()

    def on_pre_enter(self):
        # Leer archivos de la carpeta raíz
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
        if not usb_list:
            log.warning("No hay USB conectado")
            self.show_popup("AVISO", "NO HAY ALMACENAMIENTO EXTERNO CONECTADO")
            return

        usb = usb_list[0]
        files = [f for f in os.listdir(".") if f.endswith(".txt")]

        for f in files:
            export_to_usb(f, usb)
        
        if files:
            self.show_popup("AVISO", "ARCHIVOS EXPORTADOS")
    
    def borrar_archivos(self):
        files = [f for f in os.listdir(".") if f.startswith("Evento_") and f.endswith(".txt")]
        
        for fname in files:
            try:
                # Quitar solo lectura si lo tiene
                os.chmod(fname, stat.S_IWRITE)
                # Borrar archivo
                os.remove(fname)

            except PermissionError:
                self.show_popup("ERROR", f"ARCHIVO PROTEGIDO: {fname}")
                files = None
                break

            except Exception as e:
                self.show_popup("ERROR", f"NO SE HA ELIMINADO: {fname}")
                files = None
                break
        
        if not files:
            self.show_popup("AVISO", "NO HAY ARCHIVOS QUE BORRAR")
        else:
            self.show_popup("AVISO", "ARCHIVOS ELIMINADOS")

        # Actualizar lista visual
        self.ids.file_list.clear_widgets()

class FileViewerScreen(Screen):
    content = StringProperty("")

    def load_file(self, filename):
        try:
            with open(filename, "r") as f:
                self.content = f.read()
        except Exception as e:
            self.content = f"Error al abrir archivo:\n{e}"

class mainApp(App):
    def build(self):
        window_setup()
        return Builder.load_file("speed.kv")

    def on_stop(self):
        main_screen = self.root.get_screen("main")
        main_screen.deinit()

if __name__ == "__main__":
    try:
        #Builder.load_file('speed.kv')
        mainApp().run()
    except Exception as e:
        log.error(f"error de excepcion {e}")
