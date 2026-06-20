from kivy.app import App
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.lang import Builder
from kivy.clock import Clock,  mainthread
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.factory import Factory
from kivy.uix.popup import Popup
from speedmeter import SpeedMeter
from kivy.utils import get_color_from_hex

import time, threading
import os
import stat
import shutil
import hardware
import platform

SO = platform.system()
if SO == "Windows":
    LOG_DIR = "."
    try:
        import win32file
    except ImportError:
        win32file = None
else:
    LOG_DIR = "/home/pi/logs"
    win32file = None
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception as e:
        print(f"ERROR creando {LOG_DIR}: {e}")
        LOG_DIR = "."

VELOCIDAD_MAXIMA = 120 # kilometros por hora
PULSOS_POR_VUELTA = 4
PERIMETRO = 35 # en metros
TIMEOUT = 10 # segundos sin pulsos para cerrar archivo
FRENADO = 0.1

def window_setup():
    Window.size = (1024, 600)    
    Window.borderless = False
    Window.fullscreen = False
    Window.show_cursor = False
    Window.release_all_keyboards()

class MainScreen(Screen):
    speed = NumericProperty(0)
    active_file = StringProperty("")
    nextPage = BooleanProperty(False)
    
    def on_pre_enter(self):
        self.nextPage = False
        
  #variables globales
    def init_vars(self):
        self.RPM_sensor = False
        self.decay_event = None
        self.no_pulse_start = None

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
            if self.log_enabled: 
                #self.close_and_save_file()
                Clock.schedule_once(lambda dt: self.close_and_save_file(), 0)
            hardware.log.info("Pines cerrados correctamente")
            hardware.close_all_pins()

    def read_RPM(self):
        return self.RPM_sensor
        
    def on_sensor(self):
        if self.nextPage:
            return
        self.RPM_sensor = True
    
    def off_sensor(self):
        if self.nextPage:
            return
        self.RPM_sensor = False

    def simular_pulso(self):
        self.RPM_sensor = True
        time.sleep(0.01)
        self.RPM_sensor = False
    
    # hilo 
    def read_speed(self, get_RPM, _P_mts):
        self._last = None
        hardware.log.info("inicia sensor de velocidad")
        while self.running:
            # ============================
            # 1. ESPERAR FLANCO DE SUBIDA
            # ============================
            while not get_RPM():
                now_ = time.time()
                if self.last_pulse_time:
                    elapsed = now_ - self.last_pulse_time
                    # ---- INICIAR DECAIMIENTO A LOS 3s ----
                    if elapsed >= 3 and self.no_pulse_start is None:
                        self.no_pulse_start = now_
                        Clock.schedule_once(lambda _: self.start_decay(), 0)
                    # ---- TIMEOUT A LOS 10s ----
                    if elapsed >= TIMEOUT:
                        self.timed_out = True
                        self.last_pulse_time = None
                        if self.log_enabled:
                            hardware.log.info("cerrando por timeout")
                        self.close_and_save_file()
                if not self.running:
                    if self.log_enabled:
                        self.close_and_save_file()
                    return
                time.sleep(0.001)
            # ============================
            # 2. PULSO DETECTADO
            # ============================
            _now = time.time()
            self.last_pulse_time = _now
            self.timed_out = False
            # Cancelar decaimiento si estaba activo
            if self.decay_event:
                self.decay_event.cancel()
                self.decay_event = None
                self.no_pulse_start = None
            # Calcular velocidad real
            if self._last is not None:
                _dt = _now - self._last
                if _dt > 0:
                    _m_s = _P_mts / (_dt * PULSOS_POR_VUELTA)
                    _km_h = min(_m_s * 3.6, VELOCIDAD_MAXIMA)

                    Clock.schedule_once(lambda _: self.export_values(_km_h))
                    self.save_events(_km_h, _dt)
            self._last = _now
            # Esperar flanco de bajada
            while get_RPM():
                if not self.running:
                    if self.log_enabled:
                        self.close_and_save_file()
                    return
                time.sleep(0.001)

#DESACELERA
    def start_decay(self):
        if self.decay_event:
            return
        self.initial_speed = self.speed
        self.decay_event = Clock.schedule_interval(self._decay_step, FRENADO)

    def _decay_step(self, dt):
        if self.no_pulse_start is None:
            return False
        # Caida lineal suave hasta cero
        elapsed = time.time() - self.no_pulse_start
        ratio = max(0, 1 - (elapsed / TIMEOUT))
        self.speed = self.initial_speed * ratio
        if ratio == 0:
            self.decay_event = None
            self.no_pulse_start = None
            return False
        return True
# log events
    @mainthread
    def close_and_save_file(self):
        self._last = None       
        if not self.log_enabled or not self.log_filename: 
            return
        try:
            os.chmod(self.log_path, stat.S_IREAD)
            hardware.log.info(f"Archivo {self.log_filename} cerrado y puesto en solo lectura.")
            self.active_file = ""
        except Exception as e:
            hardware.log.error("Error al cerrar archivo:", e)
        self.log_enabled = False

    @mainthread
    def export_values (self, _speed):
        self.speed = _speed
    
    def save_events(self, velocidad, dt):
        if not self.log_enabled:
            dt_name = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            self.log_path = os.path.join(LOG_DIR, f"Evento_{dt_name}.txt")
            self.log_filename = f"Evento_{dt_name}.txt"
            self.log_enabled = True
            hardware.log.info(f"Nuevo archivo creado: {self.log_path}")

        self.last_pulse_time = time.time()
        dt_name = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        linea = f"Fecha y Hora = {dt_name}, Velocidad = {int(velocidad)} km/h, Tiempo = {dt:.2f} s\n"

        try:
            with open(self.log_path, "a", buffering=1) as f:
                f.write(linea)
        except Exception as e:
            hardware.log.error("Error escribiendo archivo:", e)

# nuevas pantallas

class ReusablePopup(Popup):
    title_text = StringProperty("")
    message = StringProperty("")
    on_confirm = ObjectProperty(None)
    confirm_mode = BooleanProperty(False)

def export_to_usb(source_file, usb_drive):
    try:
        destination = os.path.join(usb_drive, os.path.basename(source_file))
        shutil.copy2(source_file, destination)
    except Exception as e:
        hardware.log.warning(f"Error exportando archivo: {e}")

def get_usb_drives():
    drives = []
    media_path = "/media/pi"

    if not os.path.exists(media_path):
        return drives

    for item in os.listdir(media_path):
        full_path = os.path.join(media_path, item)
        if os.path.ismount(full_path):
            drives.append(full_path)

    return drives

class FileListScreen(Screen):
  
    def on_pre_enter(self):
        files = [ f for f in os.listdir(LOG_DIR) if f.startswith("Evento_") and f.endswith(".txt")]
        self.ids.file_list.clear_widgets()

        # Crear botones por archivo
        for fname in files:
            btn = Button(
                background_color=get_color_from_hex("#fff700"),
                text=fname,
                size_hint_y=None,
                height=40,
                on_release=lambda b, f=fname: self.open_file(os.path.join(LOG_DIR, f))
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
            self.show_popup("AVISO", "NO HAY USB CONECTADO")
            return

        usb = usb_list[0]
        files = [ os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.endswith(".txt")]

        for f in files:
            export_to_usb(f, usb)
        self.show_popup("AVISO","EVENTOS EXPORTADOS" if files else "SIN EVENTOS")
    
    def borrar_archivos(self):
        files = [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.startswith("Evento_") and f.endswith(".txt")]

        if not files:
            self.show_popup("AVISO", "SIN EVENTOS")
            return

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
                self.show_popup("ERROR", f"ARCHIVO PROTEGIDO: {os.path.basename(fname)}")
                continue

            except Exception as e:
                self.show_popup("ERROR", f"NO SE HA ELIMINADO: {os.path.basename(fname)}")
                continue

        # Actualizar lista visual
        self.ids.file_list.clear_widgets()
        #self.show_popup("AVISO", "EVENTOS ELIMINADOS")

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
        mainApp().run()
    except Exception as e:
        hardware.log.error(f"error de excepcion {e}")
    except KeyboardInterrupt:
        hardware.log.error("keyboard exit")
    finally:
        hardware.close_all_pins()
