from kivy.app import App
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.lang import Builder
from kivy.clock import Clock,  mainthread
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
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
import hora
import math

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

#constantes
REFLECTOR = 0.6
G = 9.81
longitud_pendulo = 15
#globales
timeout_juego = 30 # segundos
setter_trigger = False

def window_setup():
    Window.size = (1024, 600)    
    Window.borderless = False
    #Window.fullscreen = True
    #Window.show_cursor = False
    Window.release_all_keyboards()

def rk4_step(theta, omega, dt):
    def derivadas(th, om):
        global longitud_pendulo
        dtheta = om
        domega = -(G / longitud_pendulo) * math.sin(th)
        return dtheta, domega

    k1_t, k1_o = derivadas(theta, omega)
    k2_t, k2_o = derivadas(theta + k1_t * dt / 2, omega + k1_o * dt / 2)
    k3_t, k3_o = derivadas(theta + k2_t * dt / 2, omega + k2_o * dt / 2)
    k4_t, k4_o = derivadas(theta + k3_t * dt, omega + k3_o * dt)
    theta += dt * (k1_t + 2 * k2_t + 2 * k3_t + k4_t) / 6
    omega += dt * ( k1_o + 2 * k2_o + 2 * k3_o + k4_o) / 6

    return theta, omega
                
class MainScreen(Screen):
    speed = NumericProperty(0)
    active_file = StringProperty("")
    nextPage = BooleanProperty(False)
    RPM_sensor = BooleanProperty(False)
    needle = BooleanProperty(False)
    
    def on_pre_enter(self):
        global setter_trigger
        self.nextPage = False
        self.needle = setter_trigger
    
    def set_vel(self):
        global setter_trigger
        setter_trigger = not setter_trigger
        self.needle = setter_trigger 
        
  #variables globales
    def init_vars(self):
        self.decay_event = None
        self.no_pulse_start = None
        self.simularPulsos = None
        # Control de archivo
        self.log_enabled = False
        self.log_filename = None
        self.last_pulse_time = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.sensor = hardware.input_sensor
        self.init_vars()
        self.thread_speed = threading.Thread(
            target=self.read_speed,
            daemon=True
        )
        self.thread_speed.start()

    def deinit(self):
        self.running = False
        try:
            self.thread_speed.join(timeout=1)
            hardware.log.info("Hilos detenidos correctamente")
        except Exception as e:
            hardware.log.error(f"Error al detener los hilos: {e}")
        finally:
            if self.log_enabled: 
                self.close_and_save_file()
                Clock.schedule_once(lambda dt: self.close_and_save_file(), 0)
            hardware.log.info("Pines cerrados correctamente")
            hardware.close_all_pins()

    def read_speed(self):
        global longitud_pendulo, timeout_juego
        hardware.log.info("Inicia Hilo")
        while self.running:
            while not self.nextPage:   
                # INICIO DEL REFLECTOR
                self.sensor.wait_for_press()
                t_on = time.perf_counter()
                # FIN DEL REFLECTOR
                self.sensor.wait_for_release()
                t_off = time.perf_counter()
                ton = t_off - t_on
                if ton <= hardware.TIEMPO_TEN_MSEC:
                    continue
                # VELOCIDAD REAL MEDIDA CON TON
                mps = REFLECTOR / ton
                kph = mps * 3.6
                Clock.schedule_once(lambda _, v=kph, t=ton:self.show_speed(v, t))
                # Condiciones iniciales
                theta = 0.0
                omega = mps / longitud_pendulo
                # paso por el sensor
                start_time = time.perf_counter()
                while self.running and not self.nextPage:
                    # Si vuelve a pasar por el centro
                    if self.sensor.is_pressed:
                        break
                    elapsed = time.perf_counter() - start_time
                    if elapsed >= timeout_juego:
                        Clock.schedule_once(lambda _, t =elapsed :self.show_speed(0, t))
                        Clock.schedule_once(lambda dt: self.close_and_save_file(), 0)
                        break
                    # RK4
                    theta, omega = rk4_step(theta, omega, hardware.TIEMPO_TEN_MSEC)
                    # ------------------------
                    velocidad = abs(omega) * longitud_pendulo
                    kph = velocidad * 3.6
                    Clock.schedule_once(lambda _, v=kph, t=elapsed :self.show_speed(v, t))
                    time.sleep(hardware.TIEMPO_TEN_MSEC)
        hardware.warning.info("Fin Hilo")

# log events
    @mainthread
    def close_and_save_file(self):
        if not self.log_enabled or not self.log_filename: 
            return
        self.speed = 0
        try:
            os.chmod(self.log_path, stat.S_IREAD)
            hardware.log.info(f"Archivo {self.log_filename} cerrado y puesto en solo lectura.")
            self.active_file = ""
        except Exception as e:
            hardware.log.error("Error al cerrar archivo:", e)
        self.log_enabled = False

    @mainthread
    def show_speed (self, _speed, _time):
        self.speed = _speed
        Clock.schedule_once(lambda _: self.save_events(_speed, _time))
    
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
    cButt = BooleanProperty(False)

    def on_pre_enter(self):
        global setter_trigger
        self.cButt = setter_trigger

        files = sorted([ f for f in os.listdir(LOG_DIR) if f.startswith("Evento_") and f.endswith(".txt")], reverse=True)
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
        try:
            files = [
                os.path.join(LOG_DIR, f)
                for f in os.listdir(LOG_DIR)
                if f.startswith("Evento_") and f.endswith(".txt")
            ]

            if not files:
                self.show_popup("AVISO", "SIN EVENTOS")
                return

            self.show_popup(
                "AVISO",
                "¿DESEA ELIMINAR TODOS LOS EVENTOS?",
                on_confirm=lambda: self._borrar_archivos_confirmado(files)
            )

        except Exception as e:
            hardware.log.error(f"ERROR LEYENDO EVENTOS:\n{e}")
            self.show_popup("ERROR", "ERROR LEYENDO EVENTOS")


    def _borrar_archivos_confirmado(self, files):
        eliminados = 0
        errores = []
        for fname in files:
            try:
                hardware.log.info(f"Eliminando: {fname}")
                if os.path.exists(fname):
                    if SO == "Windows":
                        os.chmod(fname, stat.S_IWRITE)
                    os.remove(fname)
                    eliminados += 1
            except Exception as e:
                hardware.log.error(f"ERROR eliminando {fname}: {e}")
                errores.append(os.path.basename(fname))
        # Refrescar lista visual
        try:
            if "file_list" in self.ids:
                self.ids.file_list.clear_widgets()
        except Exception as e:
            hardware.log.error(f"ERROR actualizando lista: {e}")
        # Resultado final
        if errores:
            self.show_popup(
                "ERROR",
                f"SE ELIMINARON {eliminados} EVENTOS\n\n"
                f"NO SE PUDIERON ELIMINAR {len(errores)}"
            )
        else:
            self.show_popup(
                "AVISO",
                f"SE ELIMINARON {eliminados} EVENTOS"
            )

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
    
    def fecha_y_hora(self):
        content = hora.DateTimePopup()
        self.popup_dis = Popup(
            title="CONFIGURAR FECHA Y HORA",
            content=content,
            size_hint=(.90, .70), # se aumenta tamao de ventana de hora
            auto_dismiss = False
        )
        content.popup = self.popup_dis
        self.popup_dis.open()
    
    def set_data(self):
        global timeout_juego, longitud_pendulo

        if not self.cButt:
            return

        spinner_font = 22
        label_font = 24
        button_font = 26
        spinner_height = 45

        # Layout principal del popup
        layout = BoxLayout(
            orientation='vertical',
            spacing=8,
            padding=10
        )

        grid = GridLayout(cols=2, spacing=4, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        # Ancho detector
        grid.add_widget(
            Label(
                text="LONGITUD [mts]",
                font_size=30
            )
        )

        self.reflex = Spinner(
            text=str(longitud_pendulo),
            values=[str(y) for y in range(1, 31)],
            size_hint=(1, None),
            height=spinner_height,
            font_size=spinner_font
        )

        grid.add_widget(self.reflex)

        # Distancia sensor
        grid.add_widget(
            Label(
                text="TIMEOUT [seg]",
                font_size=label_font
            )
        )

        self.timeout = Spinner(
            text=str(timeout_juego),
            values=[str(m) for m in range(10, 61)],
            size_hint=(1, None),
            height=spinner_height,
            font_size=spinner_font
        )

        grid.add_widget(self.timeout)

        layout.add_widget(grid)

        btn_layout = BoxLayout(
            size_hint=(1, None),
            height=60,
            spacing=8
        )

        save_btn = Button(
            text="GUARDAR",
            font_size=button_font
        )

        save_btn.bind(on_release=self.choise_value)

        btn_layout.add_widget(save_btn)
        layout.add_widget(btn_layout)

        # Popup
        self.popup_dis = Popup(
            title='',
            title_size=0,
            content=layout,
            size_hint=(0.90, 0.50),
            auto_dismiss=True,
            separator_height=0
        )

        self.popup_dis.open()


    def choise_value(self, instance):
        global timeout_juego
        global longitud_pendulo
        global setter_trigger

        setter_trigger = False
        self.cButt = False

        longitud_pendulo = float(self.reflex.text)
        timeout_juego = float(self.timeout.text)

        hardware.log.warning(
            f"Timeout: {timeout_juego} "
            f"Distancia pendulo: {longitud_pendulo}"
        )

        if self.popup_dis:
            self.popup_dis.dismiss()

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
    
    except KeyboardInterrupt:
        hardware.log.error("keyboard exit")
    finally:
        hardware.close_all_pins()
