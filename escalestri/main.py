from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import logging
import RPi.GPIO as GPIO
import time

PIN_EMERGENCY = 18
PIN_SENSOR = 23
PIN_MARCHA = 24
PIN_BOCINA = 7
TIEMPO_SIRENA = 3
TIEMPO_1_SEC = 1

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


class Pin:
    def __init__(self, channel, mode=GPIO.OUT):
        self.channel = channel
        self.mode = mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)

        if self.mode == GPIO.IN:
            GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif self.mode == GPIO.OUT:
            GPIO.setup(self.channel, GPIO.OUT)

    def cleanup(self):
        GPIO.cleanup(self.channel)
        log.info(f"clean: pin_{self.channel}")

    def init_cb(self, my_callback):
        if self.mode == GPIO.IN:
            self.cb_on = True
            GPIO.add_event_detect(self.channel, callback=my_callback, bouncetime=200)

    def deinit_cb(self):
        if self.cb_on:
            GPIO.remove_event_detect(self.channel)
            log.info(f"denit_callback: {self.channel}")

    def turn_on(self):
        if GPIO.gpio_function(self.channel) != GPIO.OUT:
            raise RuntimeError("El pin no está configurado como salida.")
        GPIO.output(self.channel, GPIO.HIGH)  # probar que se active
        log.info(f"pin_{self.channel} ON")

    def turn_off(self):
        if GPIO.gpio_function(self.channel) != GPIO.OUT:
            raise RuntimeError("El pin no está configurado como salida.")
        GPIO.output(self.channel, GPIO.LOW)
        log.info(f"pin_{self.channel} OFF")


class Popup_banner(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):
        self.ids.label_popup.text = new_text


class viewMain(Widget):
    main_mode = None
    current_state = None
    laps = NumericProperty(0)  # Usar NumericProperty para las vueltas
    backup_laps = NumericProperty(0)  # Propiedad para el respaldo de las vueltas
    clock_event = None
    init_game = None
    init_detection = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_buttons()
        # input de boton de emergencia
        self.output_bocina = Pin(PIN_BOCINA)
        self.output_start = Pin(PIN_MARCHA)
        self.input_sensor_lap = Pin(PIN_SENSOR, GPIO.IN)
        self.input_emergency = Pin(PIN_EMERGENCY, GPIO.IN)
        self.input_emergency.init_cb(self.emergency_cb)

    def emergency_cb(self):
        log.warning("ZETA DE EMERGENCIA PRESIONADO")

    def init_buttons(self):
        for btn_id in [
            "start_button",
            "pause_button",
            "stop_button",
            "manual_button",
            "auto_button",
        ]:
            setattr(self, btn_id, self.ids[btn_id])

        self.start_button.disabled = True
        self.pause_button.disabled = True

    def power_buzzer(self):
        log.info("¡BUZZZZZ !!!!!")  # Usar logging
        self.output_bocina.turn_on()
        time.sleep(TIEMPO_SIRENA)
        self.output_bocina.turn_off()

    def special_buttons(self, button_id):
        actions = {
            "buzzer": ("bocina!", self.power_buzzer),
        }
        if button_id in actions:
            action = actions[button_id]
            action()

    def set_timers(self, id_button, dt):
        timers = {
            "button_+": 1,
            "button_-": -1,
        }
        if id_button in timers:
            increment = timers[id_button]
            self.laps = max(0, min(50, self.laps + increment))

    def on_button_press(self, button):
        self.continuous_event = None
        if self.current_state == "STOP" and self.main_mode == "AUTO":
            self.continuous_event = Clock.schedule_interval(
                partial(self.set_timers, button), 0.1
            )

    def on_button_release(self):
        if self.current_state == "STOP" and self.continuous_event:
            self.continuous_event.cancel()
            self.backup_laps = self.laps
            log.info(f"vueltas definidas: {self.laps}")

    def mode_press(self, mode_select, mode_state):
        self.backup_laps = self.laps
        self.main_mode = mode_select
        self.pause_button.disabled = True
        self.start_button.disabled = True
        self.current_state = None

        if mode_state == "down":
            self.current_state = "STOP"
            self.start_button.disabled = False

    def state_press(self, choised_state, state_value):
        if self.current_state is None:
            return

        if choised_state == "STOP":
            self.clean_all()
            return

        if choised_state == "PAUSE":
            self.current_state = "PAUSE"
            self.init_detection = False
            log.info("Pausar evento")
            self.start_button.disabled = False
            self.pause_button.disabled = True
            self.pause_button.state = "normal"
            self.output_start.turn_off()
            return

        if choised_state == "START":
            self.manual_button.disabled = True
            self.auto_button.disabled = True
            self.pause_button.disabled = False
            self.start_button.disabled = True
            self.start_button.state = "normal"

            if self.current_state == "STOP":
                self.current_state = "START"
                self.backup_laps = self.laps

                if self.main_mode == "AUTO":
                    self.laps = self.backup_laps
                elif self.main_mode == "MANUAL":
                    self.laps = 0

                self.init_game = True
                self.init_detection = True
                log.info("Iniciar evento")
                self.output_start.turn_on()
                self.input_sensor_lap.init_cb(self.counter_cb)
                return

            if self.current_state == "PAUSE":
                self.current_state = "START"
                self.init_detection = True
                log.info("Re-iniciar evento")
                return

    def counter_cb(self, ch):
        if self.init_detection:
            if self.main_mode == "MANUAL":
                self.laps += 1
            elif self.main_mode == "AUTO":
                self.laps -= 1
                if self.laps <= 0:
                    self.init_detection = False
                    self.clean_all()

    def clean_all(self):
        if self.main_mode is not None and self.init_game:
            self.power_buzzer()
            self.init_game = False

        log.info("Apagando el evento")
        self.current_state = "STOP"
        self.output_start.turn_off()
        self.input_sensor_lap.deinit_cb()

        self.manual_button.disabled = False
        self.auto_button.disabled = False
        self.start_button.disabled = False
        self.start_button.state = "normal"
        self.pause_button.disabled = True

        self.laps = self.backup_laps
        if self.main_mode == "AUTO":
            self.manual_button.state = "normal"
            self.auto_button.state = "down"
        elif self.main_mode == "MANUAL":
            self.manual_button.state = "down"
            self.auto_button.state = "normal"


class escalestriApp(App):
    def build(self):
        Window.borderless = False
        Window.fullscreen = True

        return viewMain()


if __name__ == "__main__":
    escalestriApp().run()
