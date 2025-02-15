from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import logging, time, threading
from gpiozero import Device
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import LED, Button

Device.pin_factory = PiGPIOFactory()

PIN_EMERGENCY = 2
PIN_SENSOR = 3
PIN_MARCHA = 4
PIN_BOCINA = 17
TIEMPO_SIRENA = 2
TIEMPO_1_SEC = 1
MAX_LAPS = 50

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def check_pin_free(pin):
    try:
        test_led = LED(pin)
        test_led.close()
        return True
    except Exception as e:
        log.error(f"Error al acceder al pin {pin}: {e}")
        return False


if not all(
    [
        check_pin_free(PIN_BOCINA),
        check_pin_free(PIN_MARCHA),
        check_pin_free(PIN_SENSOR),
        check_pin_free(PIN_EMERGENCY),
    ]
):
    log.error("Uno o más pines están ocupados. No puedo iniciar la aplicación.")
    raise SystemError

output_bocina = LED(PIN_BOCINA)
output_marcha = LED(PIN_MARCHA)
input_sensor = Button(PIN_SENSOR, pull_up=True)
input_emergency = Button(PIN_EMERGENCY, pull_up=True)


class myPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):
        self.ids.label_popup.text = new_text


class viewMain(Widget):
    main_mode = None
    current_state = None
    laps = NumericProperty(0)
    backup_laps = NumericProperty(0)
    current_game = None
    init_counter = None
    thread_claxon = 0
    thread_sensor = 0
    sound_claxon = None
    popup =None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_hmi_buts()

        self.output_bocina = output_bocina
        self.output_marcha = output_marcha

        self.input_sensor = input_sensor
        self.input_emergency = input_emergency

        self.thread_sensor = threading.Thread(target=self.sensor_thread, daemon=True)
        self.thread_sensor.start()
        self.thread_safety = threading.Thread(target=self.safety_thread, daemon=True)
        self.thread_safety.start()
        self.thread_claxon = threading.Thread(target=self.claxon_thread, daemon=True)
        self.thread_claxon.start()

    def sensor_thread(self):
        log.warning("inicia hilo leer sensor")
        while True:
            if not self.init_counter:
                continue
            # hay conteo
            if self.input_sensor.is_pressed:
                mode_delta = {"MANUAL": 1, "AUTO": -1}
                delta = mode_delta.get(self.main_mode, 0)
                if delta != 0:
                    self.laps = max(0, self.laps + delta)
                    log.debug(f"Modo {self.main_mode}, vueltas: {self.laps}")

            if self.laps < 0 or (self.main_mode == "AUTO" and self.laps == 0):
                self.clean_all()

    def safety_thread(self):
        show_pop_up = False
        log.info("iniciando hilo de emergencia")
        while True:
            # boton de emergencia siempre presionado
            if not input_emergency.is_pressed:
                show_pop_up = True
                self.init_counter = False
                self.current_state = "STOP"
                self.output_bocina.on()
                self.output_marcha.off()
                text = "ZETA DE EMERGENCIA PRESIONADO"
                log.warning(f"emergencia {text}")
                self.open_popup(text)

            elif show_pop_up:
                show_pop_up = False
                self.close_popup()

            time.sleep(0.1)

    def claxon_thread(self):
        log.info("iniciando hilo de sirena")
        while True:
            if self.sound_claxon:
                self.sound_claxon = False
                self.output_bocina.on()
                log.info(f"sonando Sirena {self.output_bocina.is_lit}")
                time.sleep(TIEMPO_SIRENA)
                self.output_bocina.off()

    def init_hmi_buts(self):
        for btn_id in [
            "start_button",
            "pause_button",
            "stop_button",
            "manual_button",
            "auto_button",
            "boton_bocina",
        ]:
            setattr(self, btn_id, self.ids[btn_id])

        self.start_button.disabled = True
        self.pause_button.disabled = True
        log.info("INICIANDO APP")

    def active_buzzer(self):
        output_marcha.on() if self.boton_bocina.state == "down" else output_marcha.off()
        log.info(f"bocina {self.output_bocina.is_lit}")

    def set_timers(self, id_button, dt):
        timers = {
            "button_+": 1,
            "button_-": -1,
        }
        if id_button in timers:
            increment = timers[id_button]
            self.laps = max(0, min(MAX_LAPS, self.laps + increment))

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
        log.info(f"main_mode: {self.main_mode}")
        if mode_state == "down":
            self.current_state = "STOP"
            self.start_button.disabled = False

    def state_press(self, choised_state, state_value):
        if self.current_state is None:
            return

        if choised_state == "STOP":
            self.clean_all()
            return

        elif choised_state == "PAUSE":
            self._pause_event()
            return

        elif choised_state == "START":
            self._start_event()
            return

    def _pause_event(self):
        # animicacion de botones HMI pausa
        self.start_button.disabled = False
        self.pause_button.disabled = True
        self.pause_button.state = "normal"
        log.info("Pausar evento")
        self.current_state = "PAUSE"
        self.init_counter = False
        self.output_marcha.off()
        log.info(f"marcha {self.output_marcha.is_lit}")

    def _start_event(self):
        # animacion de botones hmi
        self.manual_button.disabled = True
        self.auto_button.disabled = True
        self.pause_button.disabled = False
        self.start_button.disabled = True
        self.start_button.state = "normal"
        log.info(
            "Iniciar evento" if self.current_state == "STOP" else "Re-iniciar evento"
        )
        if self.current_state == "STOP":
            # activa sirena de inicio
            self.sound_claxon = True
            # guarda las vueltas seleccionadas
            self.backup_laps = self.laps
            # actualiza la vueltas en la HMI
            self.laps = self.backup_laps if self.main_mode == "AUTO" else 0

        self.current_state = "START"
        self.current_game = True
        self.init_counter = True
        self.output_marcha.on()
        log.info(f"marcha {self.output_marcha.is_lit}")

    def clean_all(self):
        if self.main_mode is None:
            return
        # off conteo
        log.info("-------------")
        if self.init_counter:
            self.init_counter = False
            # sonar sirena fin de juego
            self.sound_claxon = True
            log.info("FIN de juego")
        # recupero vueltas seleccionadas
        self.laps = self.backup_laps
        # parametros stop default
        self.current_state = "STOP"
        self.output_marcha.off()
        log.info(f"marcha {self.output_marcha.is_lit}")
        "animacion de los botones default"
        buttons = [self.manual_button, self.auto_button, self.start_button]
        for button in buttons:
            button.disabled = False

        self.start_button.state = "normal"
        self.pause_button.disabled = True
        modes = {
            "AUTO": self.auto_button,
            "MANUAL": self.manual_button,
        }
        for mode, button in modes.items():
            button.state = "down" if self.main_mode == mode else "normal"

        log.info(f"limpiando en modo {self.main_mode}")
        log.info("-------------")

    def open_popup(self, text: str):
        return
        if not self.popup:
            self.popup = myPopup()
            self.popup.setup_text(text)
            self.text_popup = text
            self.popup.open()

    def close_popup(self, dt):
        if self.popup:
            log.info(f"cerrando pop-up{self.text_popup}")
            self.popup.dismiss()
            self.popup = None


class vistaApp(App):
    def build(self):
        Window.borderless = False
        Window.fullscreen = False
        return viewMain()


if __name__ == "__main__":
    try:
        vistaApp().run()
    except KeyboardInterrupt:
        log.warning("Interrupcion por teclado")
        output_marcha.off()
        output_bocina.off()
    finally:
        input_emergency.close()
        input_sensor.close()
        output_bocina.close()
        output_marcha.close()
        log.info("FIN")
