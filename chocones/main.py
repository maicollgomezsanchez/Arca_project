from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import time, threading
import hardware

def window_setup():
    Window.size = (1024, 600)
    Window.borderless = True
    #Window.fullscreen = True
    #Window.show_cursor = False
    Window.release_all_keyboards()

class Popup_banner(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):
        self.ids.label_popup.text = new_text

class viewMain(Widget):  # Clase principal que maneja la interfaz y la lógica del juego
    # Variables de estado y botones
    main_mode_selected = None
    state_button_selected = None
    label_time_travel = StringProperty("00:10")  # Tiempo de viaje
    label_time_wait = StringProperty("00:10")  # Tiempo automático
    clock_event = None  # Evento de reloj para actualizar el tiempo
    coin_event = None
    travel_time = 0  # Contador de tiempo de viaje
    waiting_time = 0  # Contador de tiempo de espera
    popup = None  # Variable para manejar el popup
    game_running = None
    claxon_is_running = True
    press_claxon = False
    backup_label_time_wait = None
    backup_label_time_travel = None
    button_timers_event = None

    #guarda el ultimo valor programado de tiempo
    def save_set_time(self):
        if self.label_time_wait != "--:--":
            self.backup_label_time_wait = self.label_time_wait
        if self.label_time_wait != "--:--":
            self.backup_label_time_travel = self.label_time_travel

    # Convierte el formato de tiempo de etiqueta a segundos
    def lbl_to_time(self, lbl: str) -> int:
        mins, secs = map(int, lbl.split(":"))
        return mins * 60 + secs

    # Convierte el tiempo en segundos a formato de etiqueta (mm:ss)
    def time_to_lbl(self, time):
        return f"{time // 60:02d}:{time % 60:02d}"
    
    
    
    # funciones de  pop up
    def show_popup(self):
        self.set_marcha(False)
        Clock.schedule_once(self._open_popup, 0)

    def close_popup(self):
        if self.popup_enabled:
            self.popup_enabled = False
            self.state_button_selected = hardware.STOP
            Clock.schedule_once(self._dismiss_popup, 0)

    def _open_popup(self, dt):
        if not self.popup:
            self.popup = Popup_banner()
            self.popup.setup_text("EMERGENCIA PRESIONADA")
            self.popup.open()

    def _dismiss_popup(self, dt):
        if self.popup:
            self.popup.dismiss()
            self.popup = None
            
    def enable_popup(self, text: str, delay=0):
        self.open_popup(text)
        if delay != 0:
            self.close_popup_after_delay(delay)

    # Muestra un popup con el texto dado
    def open_popup(self, text: str):
        if not self.popup:
            self.popup = Popup_banner()

        self.popup.setup_text(text)
        self.text_popup = text
        self.popup.open()

    # Cierra el popup e de un retraso
    def close_popup_after_delay(self, delay):
        Clock.schedule_once(self.close_popup, delay)

    # Cierra el popup
    def close_popup(self, dt):
        if self.popup:
            hardware.log.info(f"cerrando pop-up{self.text_popup}")
            self.popup.dismiss()
            self.popup = None

###################################
#############  HMI
###################################
    def deinit(self):
        self.running = False
        try:
            self.claxon_loop.join(timeout=1)
            hardware.log.info("Hilos detenidos correctamente")
        except Exception as e:
            hardware.log.error(f"Error al detener los hilos: {e}")
        finally:
            hardware.close_all_pins()

    # Inicializa los botones de la interfaz
    def init_buttons(self):
        for name in (
            "start_button", "pause_button", "stop_button",
            "coin_button", "decoin_button",
            "manual_button", "semi_button", "auto_button"
        ):
            if name in self.ids: setattr(self, name, self.ids[name])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_buttons()
        self.output_bocina = hardware.output_bocina
        self.thread_buzzer = None
        self.thread_coin = None
        #hilo de bocina
        self.thread_claxon = threading.Thread(target=self.claxon_loop, daemon=True)
        if not self.thread_claxon.is_alive():
            self.thread_claxon.start()
    
        #hardware.input_emergency.when_pressed = self.close_popup
        #hardware.input_emergency.when_released = self.show_popup

# capa hardware
    def set_marcha(self, estado: bool):
        hm = hardware.output_marcha
        if hm.is_lit != estado:
            hm.on() if estado else hm.off()
            hardware.log.info(f"Marcha {hm.is_lit}")

    def set_bocina(self, estado: bool):
        hm = hardware.output_bocina
        if hm.is_lit != estado:
            hm.on() if estado else hm.off()
            hardware.log.info(f"BOcina {hm.is_lit}")
        
    def claxon_loop(self):
        hardware.log.info("iniciando hilo de bocina")
        while self.claxon_is_running:
            time.sleep(0.1)
            try:
                if self.press_claxon:
                    self.set_bocina(True)
                    hardware.log.info("sonando Bocina !!!")
                    time.sleep(hardware.TIEMPO_DURACION_SIRENA)
                    self.set_bocina(False)
                    self.press_claxon = False

            except Exception as e:
                hardware.log.error(f"Error en claxon_thread: {e}")
                self.set_bocina(False)

    # consumo de una moneda
    def eating_coin(self, dt=None):
        if self.decoin_button.state == "down":
            return
        if self.coin_event is None:
            self.pulse_count = 0
            self.pulse_on = False
            self.coin_event = Clock.schedule_interval( self._coin_pulse_cycle,hardware.TIEMPO_PULSOS_FICHA)

    def _coin_pulse_cycle(self, dt):
        self.pulse_on = not self.pulse_on
        if self.pulse_on:
            hardware.output_traga_ficha.on()
            hardware.log.info(f"Comiendo ficha x {self.pulse_count + 1}")
            return
        hardware.output_traga_ficha.off()
        self.pulse_count += 1
        if self.pulse_count >= hardware.MAXIMO_PULSOS_FICHA:
            if self.coin_event:
                self.coin_event.cancel()
                self.coin_event = None

    def decoin_press(self):
        if self.decoin_button.state == "down":
            hardware.log.info("COIN BUTTON BLOCKED")
            self.coin_button.disabled = True
        else:
            self.coin_button.disabled = False

    # BOTONES DE SUBIR Y BAJAR CONTADORES
    def set_times(self, id_button, dt):
        if self.main_mode_selected == "MANUAL":
            return

        timers = {
            "travel_+": ("label_time_travel", 1),
            "travel_-": ("label_time_travel", -1),
            "auto_+": ("label_time_wait", 1),
            "auto_-": ("label_time_wait", -1),
        }
        if id_button in timers:
            label, increment = timers[id_button]
            current_time = getattr(self, label, "00:00")
            current_time = self.lbl_to_time(current_time)

        new_time = max(0, current_time + increment)

        if label == "label_time_wait":
            if self.main_mode_selected == "AUTO":
                current_time = min(hardware.TIEMPO_MAXIMO_ESPERA, new_time)
        else:
            current_time = new_time

        setattr(self, label, self.time_to_lbl(current_time))

    def on_button_press(self, button):
        if self.state_button_selected == "STOP":
            self.button_timers_event = Clock.schedule_interval(partial(self.set_times, button), 0.1)

    def on_button_release(self):
        if self.button_timers_event:
            self.button_timers_event.cancel()
            self.save_set_time()

    # selecciona el modo del juego
    def mode_press(self, mode_select): 
        if all(
            btn.state == "normal"
            for btn in [
                self.start_button,
                self.auto_button,
                self.manual_button,
                self.semi_button,
            ]
        ):
            self.label_time_travel = self.backup_label_time_travel
            self.label_time_wait = self.backup_label_time_wait
            self.main_mode_selected = None
            return

        self.save_set_time()

        if mode_select == "MANUAL":
            self.label_time_wait = "--:--"
            self.label_time_travel = "--:--"

        elif mode_select == "SEMI":
            self.label_time_wait = "--:--"
            self.label_time_travel = self.backup_label_time_travel

        elif mode_select == "AUTO":
            self.label_time_wait = self.backup_label_time_wait
            self.label_time_travel = self.backup_label_time_travel
        
        self.main_mode_selected = mode_select
        self.state_button_selected = "STOP"


    # Cambia el estado del sistema
    def state_press(self, state_select):
        if self.main_mode_selected is None:
            return

        if state_select == "STOP":
            self.clean_all()
            return

        if state_select == "START":
            for btn in (
            self.manual_button,
            self.semi_button,
            self.auto_button,
            self.start_button,): btn.disabled = True
            self.pause_button.disabled = False
            self.start_button.state = "normal"
            
            if self.state_button_selected == "STOP":
                self.save_set_time()
                self.init_counter()

            elif self.state_button_selected == "PAUSE":
                self.state_button_selected = "START"

                callback = self.start_travel_time
                if self.main_mode_selected == "AUTO":
                    callback = self.start_waiting_time

                self.clock_event = Clock.schedule_interval(callback, 1)
            return

        if state_select == "PAUSE":
            hardware.log.info(f"pausado en modo: {self.main_mode_selected}")
            #apagando marcha si esta encendido
            self.set_marcha(False)
            self.start_button.disabled = False
            self.pause_button.disabled = True
            self.pause_button.state = "normal"
            self.state_button_selected = "PAUSE"
            # pausa el contador sin reiniciar el label
            Clock.unschedule(self.clock_event)
            return

        raise ValueError("error states")

# Inicializa los contadores de tiempo
    def init_counter(self):
        if self.state_button_selected != "STOP":
            return

        self.state_button_selected = "START"
        self.game_running = True

        mode = self.main_mode_selected

        self.travel_time = self.lbl_to_time(self.backup_label_time_travel)
        self.waiting_time = 0
        if mode == "AUTO":
            self.waiting_time = self.lbl_to_time(self.backup_label_time_wait)
            hardware.log.info("Conteo de espera en modo AUTO")
            self.clock_event = Clock.schedule_interval(self.start_waiting_time, 1)
            return

        if mode == "MANUAL":
            self.travel_time = 0

        # Común a MANUAL y SEMI
        self.press_claxon = True
        Clock.schedule_once(
            self.start_travel_after_buzzer,
            hardware.TIEMPO_DURACION_SIRENA
        )

    def start_travel_after_buzzer(self, dt):
        hardware.log.info(f"Comienza el juego en {self.main_mode_selected}")
        self.clock_event = Clock.schedule_interval(self.start_travel_time, 1)

    # Actualiza el tiempo de espera (decrece)
    def start_waiting_time(self, dt):
        if self.state_button_selected == "START":
            self.waiting_time = self.waiting_time - 1
            self.label_time_wait = self.time_to_lbl(self.waiting_time)
            if self.waiting_time <= 0:
                # hace sonar la bocina por dos segundos y espera
                hardware.log.info("Finaliza espera en modo AUTO inicia temporizador")
                self.press_claxon = True
                if self.clock_event:
                    self.clock_event.cancel()
                    self.clock_event = None
                Clock.schedule_once(self.end_wainting_time_and_continue, hardware.TIEMPO_DURACION_SIRENA)

    def end_wainting_time_and_continue(self, dt):
        self.label_time_wait = self.backup_label_time_wait
        self.clock_event = Clock.schedule_interval(self.start_travel_time, 1)
        
    # Actualiza el tiempo de viaje
    def start_travel_time(self, dt):
        if self.state_button_selected != "START":
            return
        #enciende marcha
        self.set_marcha(True)
        # Actualizar contador según el modo
        self.travel_time = max(
            0,
            (
                self.travel_time + 1
                if self.main_mode_selected == "MANUAL"
                else self.travel_time - 1
            ),
        )
        self.label_time_travel = self.time_to_lbl(self.travel_time)
        # Si no es modo MANUAL y el contador llega a 0
        if self.travel_time == 0:
            self.label_time_travel = "00:00"
            hardware.log.info(f"Finaliza en {self.main_mode_selected}")
            if self.main_mode_selected == "SEMI":
                self.clean_all()

            elif self.main_mode_selected == "AUTO":
                self.eating_coin()

                if self.clock_event:
                    self.clock_event.cancel()
                    self.clock_event = None
                self.state_button_selected = "STOP"
                #suena bocina
                self.press_claxon = True
                # Programar continuacion en 2 segundos
                Clock.schedule_once(self.end_travel_and_init, hardware.TIEMPO_DURACION_SIRENA)

    def end_travel_and_init(self, dt):
        self.label_time_travel = self.backup_label_time_travel
        self.init_counter()

    # Limpia todos los estados y reinicia los temporizadores
    def clean_all(self):
        if self.main_mode_selected is None:
            return
        # apaga la marcha
        self.set_marcha(False)
        
        if self.game_running:
            self.game_running = False
            self.press_claxon = True
            Clock.schedule_once(self.eating_coin, hardware.TIEMPO_DURACION_SIRENA)
        # Restaurar etiquetas y detener el temporizador
        self.label_time_travel = self.backup_label_time_travel
        self.label_time_wait =self.backup_label_time_wait
    
        #limpia contadores si los hubiera
        if self.clock_event:
            self.clock_event.cancel()
            self.clock_event = None

        # Habilitar botones HMI
        for button in [
            self.manual_button,
            self.semi_button,
            self.auto_button,
            self.start_button,
            self.pause_button,
        ]: button.disabled = False
        #restablece modo de juego

        modes = {
            "AUTO": self.auto_button,
            "MANUAL": self.manual_button,
            "SEMI": self.semi_button,
        }
        for mode, button in modes.items():
            button.state = "down" if self.main_mode_selected == mode else "normal"
        self.state_button_selected = None

class gameApp(App):
    def build(self):
        window_setup()
        self.app_widget = viewMain()
        return self.app_widget

    def on_stop(self):
        self.app_widget.deinit()


if __name__ == "__main__":
    try:
        gameApp().run()
    
    except KeyboardInterrupt:
        hardware.log.error("keyboard exit")
    finally:
        hardware.close_all_pins()