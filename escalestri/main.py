from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import time, threading
from hardware import (
    log,
    input_emergency,
    input_sensor,
    input_remote_paro,
    input_remote_bocina,
    input_remote_marcha,
    input_remote_pausa,
    output_marcha,
    output_bocina,
    TIEMPO_SIRENA,
    BOUNCE_TIME,
    MAX_LAPS,
    START,
    STOP,
    PAUSE,
    AUTO,
    MANUAL,
    close_all_pins,
)


class Popup_banner(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):
        self.ids.label_popup.text = new_text


class viewMain(Widget):
    main_mode = None
    current_state = None
    laps = NumericProperty(0)
    backup_laps = NumericProperty(0)
    init_counter = False
    sensor_pressed = False
    thread_claxon = 0
    sound_claxon = False
    popup = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.init_hmi_buts()
        self.output_bocina = output_bocina
        self.thread_claxon = threading.Thread(target=self.claxon_thread, daemon=True)
        self.thread_claxon.start()
        # funciones de botones externos
        input_sensor.when_released = self.off_sensor
        input_sensor.when_pressed = self.on_sensor

        input_emergency.when_pressed = self.close_popup
        # input_emergency.when_released = self.show_popup

        # inicia funciones de botones remotos
        output_bocina.source = input_remote_bocina

        """
        input_remote_marcha.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self._remote_marcha(), 0
        )
        input_remote_pausa.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self._remote_pausa(), 0
        )
        input_remote_paro.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self._remote_paro(), 0
        )
        """

    def deinit(self):
        self.running = False
        try:
            self.thread_claxon.join()
            log.info("Hilos detenidos correctamente")
        except Exception as e:
            log.error(f"Error al detener los hilos: {e}")
        finally:
            close_all_pins()
            log.info("Pines cerrados correctamente")

    # funciones de botones externos
    def on_sensor(self):
        if not self.sensor_pressed:
            self.sensor_pressed = True
            if not self.init_counter:
                return
            # cambia la variable cuando presiona el boton
            mode_delta = {MANUAL: 1, AUTO: -1}
            delta = mode_delta.get(self.main_mode, 0)
            if delta != 0:
                self.laps = max(0, self.laps + delta)
                log.debug(f"Modo {self.main_mode}, vueltas: {self.laps}")
            # cerrar si llega a limites
            if (self.main_mode == MANUAL and self.laps >= MAX_LAPS) or (
                self.main_mode == AUTO and self.laps <= 0
            ):
                self.init_counter = False
                self.clean_all()

    def off_sensor(self):
        if self.sensor_pressed:
            self.sensor_pressed = False

    def _remote_marcha(self):
        log.warning("marcha por remoto")
        self.state_press(START)

    def _remote_paro(self):
        log.warning("paro por remoto")
        self.state_press(STOP)

    def _remote_pausa(self):
        log.warning("pausa por remoto")
        self.state_press(PAUSE)

    # funciones de  pop up
    def show_popup(self):
        self.init_counter = False
        output_marcha.off()
        output_bocina.off()
        log.info("SIRENA EMERGENCIA !!!")
        Clock.schedule_once(self._open_popup, 0)

    def close_popup(self):
        self.current_state = STOP
        Clock.schedule_once(self._dismiss_popup, 0)

    def _open_popup(self, dt):
        if not self.popup:
            self.popup = Popup_banner()
            self.popup.setup_text("ZETA DE EMERGENCIA PRESIONADO")
            self.popup.open()

    def _dismiss_popup(self, dt):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def claxon_thread(self):
        log.info("iniciando hilo de sirena")
        while self.running:
            time.sleep(0.1)
            try:
                if self.sound_claxon:
                    self.sound_claxon = False
                    output_bocina.on()
                    log.info("sonando Bocina !!!")
                    time.sleep(TIEMPO_SIRENA)
                    output_bocina.off()

            except Exception as e:
                log.error(f"Error en claxon_thread: {e}")
                output_bocina.off()

    def init_hmi_buts(self):
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

        self.buttons = [self.manual_button, self.auto_button, self.start_button]
        self.modes = {
            AUTO: self.auto_button,
            MANUAL: self.manual_button,
        }
        log.info("INICIANDO APP")

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
        if self.current_state == STOP:
            self.continuous_event = Clock.schedule_interval(
                partial(self.set_timers, button), 0.1
            )

    def on_button_release(self):
        if self.current_state == STOP and self.continuous_event:
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
            self.current_state = STOP
            self.start_button.disabled = False

    def state_press(self, choised_state):
        if self.current_state is None:
            return
        if choised_state == STOP:
            self.clean_all()
            return
        elif choised_state == PAUSE:
            self._pause_event()
            return
        elif choised_state == START:
            self._start_event()
            return

    def _pause_event(self):
        # animicacion de botones HMI pausa
        self.start_button.disabled = False
        self.pause_button.disabled = True
        self.pause_button.state = "normal"
        log.info("Pausar evento")
        self.current_state = PAUSE
        self.init_counter = False
        output_marcha.off()

    def _start_event(self):
        # animacion de botones hmi
        self.manual_button.disabled = True
        self.auto_button.disabled = True
        self.pause_button.disabled = False
        self.start_button.disabled = True
        self.start_button.state = "normal"
        log.info(
            "Iniciar evento" if self.current_state == STOP else "Re-iniciar evento"
        )
        if self.current_state == STOP:
            # activa sirena de inicio
            self.sound_claxon = True
            # guarda las vueltas seleccionadas
            self.backup_laps = self.laps
            # actualiza la vueltas en la HMI
            self.laps = self.backup_laps if self.main_mode == AUTO else 0
        self.current_state = START
        self.init_counter = True
        output_marcha.on()

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
        self.current_state = STOP
        output_marcha.off()
        "animacion de los botones default"
        for button in self.buttons:
            button.disabled = False
        self.start_button.state = "normal"
        self.pause_button.disabled = True
        for mode, button in self.modes.items():
            button.state = "down" if self.main_mode == mode else "normal"
        log.info(f"limpiando en modo {self.main_mode}")
        log.info("-------------")


class vistaApp(App):
    def build(self):
        Window.borderless = False
        Window.fullscreen = False
        return viewMain()

    def on_stop(self):
        # Llamar a deinit() explícitamente
        app_widget = self.root
        app_widget.deinit()


if __name__ == "__main__":
    try:
        vistaApp().run()
    except Exception as e:
        log.error(f"error de excepcion {e}")
