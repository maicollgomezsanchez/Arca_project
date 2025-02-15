#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import logging, time, threading

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)
# pin de entrada
PIN_EMERGENCY = 3
PIN_SENSOR = 4
# PINES de salida
PIN_MARCHA = 17
PIN_BOCINA = 27
PIN_TRAGA_MONEDA = 22
# TIEMPOS
TIEMPO_SIRENA = 2  # Tiempo de duración de la sirena en segundos
TIEMPO_1_SEC = 1
TIEMPO_MAXIMO_ESPERA = 600  # mins en seg


class Popup_banner(Popup):  # Clase para la ventana emergente (popup)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):  # Establece el texto que se muestra en el popup
        self.ids.label_popup.text = new_text


class Pin:
    def __init__(self, channel, mode="GPIO.OUT"):
        self.channel = channel
        self.mode = mode
        log.warning(f"init pin {self.channel} in {self.mode} mode")
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        """
        if self.mode == "GPIO.IN":
            #GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            return
        if self.mode == "GPIO.OUT":
            #GPIO.setup(self.channel, GPIO.OUT)
            self.turn_off()

    def cleanup(self):
        # GPIO.cleanup(self.channel)
        log.warning(f"clean: pin_{self.channel}")

    def init_cb(self, cb_up, cb_down=None):
        if self.mode == "GPIO.IN":
            log.warning(f"init callback up {self.channel}")
            # GPIO.add_event_detect(self.channel, GPIO.RISING, callback=cb_up, bouncetime=200)  # Flanco de subida (LOW a HIGH)
        if cb_down is not None:
            # GPIO.add_event_detect(self.channel, GPIO.FALLING, callback=cb_down, bouncetime=200)  # Flanco de bajada (HIGH a LOW)
            log.warning(f"init callback down {self.channel}")
        else:
            self.cb_on = True

    def deinit_cb(self):
        if self.cb_on:
            # GPIO.remove_event_detect(self.channel)
            log.warning(f"de-init_callback: {self.channel}")

    def toggle_pin(self, delay, repeat=0):
        if repeat == 0:
            self.turn_on()
            time.sleep(delay)
            self.turn_off()
            return
        
        while repeat > 0:
            self.turn_on()
            time.sleep(delay)
            self.turn_off()
            repeat -= 1

    def turn_on(self):
        #GPIO.output(self.channel, GPIO.HIGH)
        log.warning(f"turn_on_pin {self.channel}")

    def turn_off(self):
        #GPIO.output(self.channel, GPIO.LOW)
        log.warning(f"turn_off_pin {self.channel}")


class viewMain(Widget):  # Clase principal que maneja la interfaz y la lógica del juego
    # Variables de estado y botones
    main_mode = None
    current_state = None
    label_time_travel = ObjectProperty("05:00")  # Tiempo de viaje
    label_time_wait = ObjectProperty("09:30")  # Tiempo automático
    clock_event = None  # Evento de reloj para actualizar el tiempo
    counter_travel = 0  # Contador de tiempo de viaje
    counter_wait = 0  # Contador de tiempo de espera
    popup = None  # Variable para manejar el popup
    current_game = None

    # lanza el pop-up de emergencia
    def show_popup_emergency(self):
        self.output_marcha.turn_off()
        self.power_buzzer()
        text = "ZETA DE EMERGENCIA PRESIONADO"
        log.warning(text)
        self.enable_popup(text)

    # Activa la bocina
    def power_buzzer(self):
        if self.thread_buzzer and self.thread_buzzer.is_alive():
            return

        log.info("¡BUZZZZZ !!!!!")
        self.thread_buzzer = threading.Thread(
            target=self.output_bocina.toggle_pin, args=(TIEMPO_SIRENA,), daemon=True
        )
        self.thread_buzzer.start()

    # Simula el consumo de una moneda
    def eating_coin(self):
        if self.thread_coin and self.thread_coin.is_alive():
            return
        log.info("eating_coin")
        self.thread_coin = threading.Thread(
            target=self.output_moneda.toggle_pin,
            args=(TIEMPO_1_SEC / 3, 3),
            daemon=True,
        )
        self.thread_coin.start()
        # Configura los tiempos de respaldo

    def setup_time(self):
        self.backup_label_wait = self.label_time_wait
        self.backup_label_travel = self.label_time_travel

    # Convierte el formato de tiempo de etiqueta a segundos
    def lbl_to_time(self, lbl: str) -> int:
        mins, secs = map(int, lbl.split(":"))
        return mins * 60 + secs

    # Convierte el tiempo en segundos a formato de etiqueta (mm:ss)
    def time_to_lbl(self, time):
        return f"{time // 60:02d}:{time % 60:02d}"

    # Gestiona los botones especiales como buzzer y moneda
    def special_buttons(self, button_id):
        actions = {
            "buzzer": (self.power_buzzer),
            "coin": (self.eating_coin),
        }

        if button_id in actions:
            action = actions[button_id]
            action()

    # Maneja la acción de presionar el botón de "decoin"
    def decoin_press(self):
        if self.current_state in ("STOP", None):
            if self.decoin_button.state == "normal":
                self.coin_button.disabled = True
                log.info("COIN BUTTON BLOCKED")
            else:
                self.coin_button.disabled = False

    # BOTONES DE SUBIR Y BAJAR CONTADORES
    def set_counters(self, id_button, dt):
        if self.main_mode == "MANUAL":
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
            if self.main_mode == "AUTO":
                current_time = min(TIEMPO_MAXIMO_ESPERA, new_time)

        else:
            current_time = new_time
        # log.info(f"new time {label}: {self.time_to_lbl(current_time)}")
        setattr(self, label, self.time_to_lbl(current_time))

    def on_button_press(self, button):
        if self.current_state == "STOP":
            self.continuous_event = Clock.schedule_interval(
                partial(self.set_counters, button), 0.1
            )

    def on_button_release(self):
        if self.current_state == "STOP" and self.continuous_event:
            self.continuous_event.cancel()
            self.setup_time()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_buttons()
        # inputs
        self.input_emergency = Pin(PIN_EMERGENCY, "GPIO.IN")
        self.input_emergency.init_cb(
            cb_up=self.show_popup_emergency, cb_down=self.close_popup
        )
        # outputs
        self.output_bocina = Pin(PIN_BOCINA)
        self.thread_buzzer = None
        self.thread_coin = None
        self.output_marcha = Pin(PIN_MARCHA)
        self.output_moneda = Pin(PIN_TRAGA_MONEDA)

    # Inicializa los botones de la interfaz
    def init_buttons(self):
        buttons = [
            "start_button",
            "pause_button",
            "stop_button",
            "coin_button",
            "decoin_button",
            "manual_button",
            "semi_button",
            "auto_button",
        ]

        for btn_id in buttons:
            setattr(self, btn_id, self.ids[btn_id])

        self.start_button.disabled = True
        self.pause_button.disabled = True
        self.coin_button.disabled = True

    # Cambia el modo de operación
    def mode_press(self, mode_select, mode_state):
        self.setup_time()
        self.main_mode = mode_select
        self.current_state = "STOP"
        self.pause_button.disabled = True
        self.start_button.disabled = True

        if mode_state == "down":
            self.start_button.disabled = False

    # Cambia el estado del sistema
    def state_press(self, state_select, state_value):
        if self.current_state is None:
            return

        if state_select == "STOP":
            self.clean_all()
            return

        if state_select == "START":
            self.manual_button.disabled = True
            self.semi_button.disabled = True
            self.auto_button.disabled = True
            self.coin_button.disabled = True
            self.start_button.disabled = True
            self.pause_button.disabled = False
            self.start_button.state = "normal"

            if self.current_state == "STOP":
                self.setup_time()
                self.init_counter()

            elif self.current_state == "PAUSE":
                self.current_state = "START"
                self.clock_event = Clock.schedule_interval(
                    (
                        self.update_wait_time
                        if self.main_mode == "AUTO"
                        else self.update_travel_time
                    ),
                    1,
                )

            return

        if state_select == "PAUSE":
            log.info(f"pausado en modo: {self.main_mode}")
            self.output_marcha.turn_off()

            self.start_button.disabled = False
            self.pause_button.disabled = True
            self.pause_button.state = "normal"
            self.current_state = "PAUSE"
            Clock.unschedule(self.clock_event)
            return

        raise ValueError("error states")

    # Inicializa los contadores de tiempo
    def init_counter(self):
        if self.current_state != "STOP":
            raise ValueError("Error en init_counter")

        self.current_state = "START"
        self.current_game = True

        self.label_time_travel = (
            self.backup_label_travel if self.main_mode != "MANUAL" else "00:00"
        )
        self.label_time_wait = self.backup_label_wait

        self.counter_wait = self.lbl_to_time(self.backup_label_wait)
        self.counter_travel = (
            0
            if self.main_mode == "MANUAL"
            else self.lbl_to_time(self.backup_label_travel)
        )

        if self.main_mode == "AUTO":
            log.info("Conteo de espera en modo AUTO")
            self.clock_event = Clock.schedule_interval(self.update_wait_time, 1)
            return

        # Activar el buzzer si es necesario
        self.active_buzzer = True
        if self.active_buzzer:
            self.active_buzzer = False
            log.info(f"Comienza el juego en {self.main_mode}")
            self.power_buzzer()

        self.clock_event = Clock.schedule_interval(self.update_travel_time, 1)

    # Actualiza el tiempo de espera (decrece)
    def update_wait_time(self, dt):
        if self.current_state == "START":
            self.counter_wait = max(0, self.counter_wait - 1)
            self.label_time_wait = self.time_to_lbl(self.counter_wait)

            if self.counter_wait == 0:
                if self.active_buzzer:
                    self.active_buzzer = False
                    self.power_buzzer()

                log.info("Finaliza espera en modo AUTO inicia temporizador")
                self.clock_event.cancel()
                self.clock_event = Clock.schedule_interval(self.update_travel_time, 1)

    # Actualiza el tiempo de viaje
    def update_travel_time(self, dt):
        if self.current_state != "START":
            return
        self.output_marcha.turn_on()
        # Actualizar contador según el modo
        self.counter_travel = max(
            0,
            (
                self.counter_travel + 1
                if self.main_mode == "MANUAL"
                else self.counter_travel - 1
            ),
        )
        self.label_time_travel = self.time_to_lbl(self.counter_travel)

        # Si no es modo MANUAL y el contador llega a 0
        if self.main_mode != "MANUAL" and self.counter_travel == 0:
            self.label_time_travel = "00:00"
            log.info(f"Finaliza en {self.main_mode}")
            if self.main_mode == "SEMI":
                self.clean_all()

            elif self.main_mode == "AUTO":
                if self.decoin_button.state == "down":
                    self.eating_coin()

                self.clock_event.cancel()
                self.current_state = "STOP"
                self.power_buzzer()
                self.init_counter()

    # Limpia todos los estados y reinicia los temporizadores
    def clean_all(self):
        if self.main_mode is None:
            return

        # Restaurar etiquetas y detener el temporizador
        self.label_time_travel, self.label_time_wait = (
            self.backup_label_travel,
            self.backup_label_wait,
        )
        Clock.unschedule(self.clock_event)
        self.current_state = "STOP"
        # apaga la marcha
        self.output_marcha.turn_off()

        # Habilitar botones
        for button in [
            self.manual_button,
            self.semi_button,
            self.auto_button,
            self.start_button,
        ]:
            button.disabled = False

        self.start_button.state = "normal"
        self.pause_button.disabled = True

        if self.decoin_button.state == "down":
            self.coin_button.disabled = False

        # Configurar estado de botones según el modo
        modes = {
            "AUTO": self.auto_button,
            "MANUAL": self.manual_button,
            "SEMI": self.semi_button,
        }
        for mode, button in modes.items():
            button.state = "down" if self.main_mode == mode else "normal"
        log.info(f"limpiando en modo {self.main_mode}")
        # Acciones finales si el juego estaba activo
        if self.current_game:
            self.eating_coin()
            self.power_buzzer()
            self.current_game = False

    # Manejo de popups
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

    # Cierra el popup después de un retraso
    def close_popup_after_delay(self, delay):
        Clock.schedule_once(self.close_popup, delay)

    # Cierra el popup
    def close_popup(self, dt):
        if self.popup:
            log.info(f"cerrando pop-up{self.text_popup}")
            self.popup.dismiss()
            self.popup = None


# Clase principal de la aplicación Kivy
class carruselApp(App):
    def build(self):
        # Configura la ventana sin bordes
        Window.borderless = False
        # Descomentar para pantalla completa
        Window.fullscreen = False
        return viewMain()


# Ejecuta la aplicación
if __name__ == "__main__":
    carruselApp().run()
