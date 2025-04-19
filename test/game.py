from kivy.app import App # type: ignore
from kivy.uix.widget import Widget # type: ignore
from kivy.properties import NumericProperty # type: ignore
from kivy.uix.popup import Popup # type: ignore
from kivy.clock import Clock # type: ignore
from kivy.core.window import Window # type: ignore
from functools import partial
import time, threading
import logging

from kivy.lang import Builder

Builder.load_file('game.kv')

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


MAX_LAPS = 50
TIEMPO_SIRENA = 2


START, STOP, PAUSE, MANUAL, AUTO, SEMI = (
    "START",
    "STOP",
    "PAUSE",
    "MANUAL",
    "AUTO",
    "SEMI",
)


def window_setup():
    Window.borderless = False
    Window.fullscreen = False
    Window.show_cursor = True
    Window.release_all_keyboards()
    


class Popup_banner(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):
        self.ids.label_popup.text = new_text


class viewMain(Widget):
    laps = NumericProperty(0)
    backup_laps = NumericProperty(0)
  
    def init_vars (self):
        self.main_mode = None
        self.current_state = None
        self.init_counter = False
        self.sensor_pressed = False
        self.sound_claxon = False
        self.popup = None
        self.popup_enabled = False
        self.widget_buzzer = False
        self.continuous_event = None
        self.buttons_name = [
            "start_button",
            "pause_button",
            "stop_button",
            "manual_button",
            "auto_button",
            "bocina_button",
            "mayor_button",
            "minus_button",
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.init_vars()
        self.init_hmi_buts()
        self.thread_claxon = threading.Thread(target=self.claxon_thread, daemon=True)
        self.thread_claxon.start()

    def deinit(self):
        self.running = False
        try:
            self.thread_claxon.join()
            log.info("Hilos detenidos correctamente")
        except Exception as e:
            log.error(f"Error al detener los hilos: {e}")
        finally:
            log.info("Pines cerrados correctamente")

    # funciones de botones externos
    def on_sensor(self):
        if not self.sensor_pressed:
            self.sensor_pressed = True

            if not self.init_counter:
                return
            mode_delta = {MANUAL: 1, AUTO: -1}
            delta = mode_delta.get(self.main_mode, 0)

            if delta != 0:
                self.laps = max(0, self.laps + delta)
                log.debug(f"Modo {self.main_mode}, vueltas: {self.laps}")
            # cerrar si llega a limites
            limit_manual = self.main_mode == MANUAL and self.laps == MAX_LAPS
            limit_auto = self.main_mode == AUTO and self.laps == 0

            if limit_auto or limit_manual:
                self.clean_all()

    def off_sensor(self):
        if self.sensor_pressed:
            self.sensor_pressed = False

    def _remote_marcha(self):
        log.warning("marcha por remoto")
        self.state_event(START)

    def _remote_paro(self):
        log.warning("paro por remoto")
        self.state_event(STOP)

    def _remote_pausa(self):
        log.warning("pausa por remoto")
        self.state_event(PAUSE)

    # funciones de  pop up
    def show_popup(self):
        if not self.popup_enabled:
            self.popup_enabled = True
            self.init_counter = False
            self.off_buzzer()
            self.clean_all()
            log.info("SIRENA EMERGENCIA !!!")
            Clock.schedule_once(self._open_popup, 0)

    def close_popup(self):
        if self.popup_enabled:
            self.popup_enabled = False
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
                    self.on_buzzer()
                    time.sleep(TIEMPO_SIRENA)
                    self.off_buzzer()

            except Exception as e:
                log.error(f"Error en claxon_thread: {e}")
                self.off_buzzer()

    # funciones HMI
    def init_hmi_buts(self):
        for ids in self.buttons_name:
            setattr(self, ids, self.ids[ids])
        self.start_button.disabled = True
        self.pause_button.disabled = True

        self.buttons_id = [self.manual_button, self.auto_button, self.start_button]
        self.modes = {
            AUTO: self.auto_button,
            MANUAL: self.manual_button,
        }

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if not self.collide_point(*touch.pos):
                self.on_touch_up(touch)
                touch.ungrab(self)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.widget_buzzer:
            self.widget_buzzer = False
            self.off_buzzer()
        if self.current_state == STOP and self.continuous_event:
            self.continuous_event.cancel()
            self.backup_laps = self.laps
            log.info(f"vueltas definidas: {self.laps}")
        return super().on_touch_up(touch)

    def on_touch_down(self, touch):
        for widget_id in self.buttons_name:
            btn = self.ids[widget_id]
            if btn.collide_point(*touch.pos):
                touch.grab(self)

                if widget_id == "bocina_button":
                    self.widget_buzzer = True
                    self.on_buzzer()
                    return super().on_touch_down(touch)
        
                if widget_id == "stop_button":
                    self.state_event(STOP)
                    return super().on_touch_down(touch)
                
                if self.current_state in (STOP, None):
                    if widget_id == "manual_button" and self.main_mode is not MANUAL:
                        self.mode_press(MANUAL, btn)
                        return super().on_touch_down(touch)

                    if widget_id == "auto_button" and self.main_mode is not AUTO:
                        self.mode_press(AUTO, btn)
                        return super().on_touch_down(touch)
                
                if self.current_state is STOP:
                    if widget_id in ("mayor_button", "minus_button"):
                        self.on_button_press(widget_id)
                        return super().on_touch_down(touch)

                if self.current_state in (STOP, PAUSE):
                    if widget_id == "start_button":
                        self.state_event(START)
                        return super().on_touch_down(touch)

                if self.current_state is START:
                    if widget_id == "pause_button":
                        self.state_event(PAUSE)
                        return super().on_touch_down(touch)
        return False

    def on_buzzer(self):
        log.info("bocina on!")

    def off_buzzer(self):
        log.info("bocina off!")

    def set_timers(self, id_button, dt):
        timers = {
            "mayor_button": 1,
            "minus_button": -1,
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

    def mode_press(self, mode, state):
        self.backup_laps = self.laps
        self.main_mode = mode
        log.info(f"main_mode: {self.main_mode}")
        self.pause_button.disabled = True
        self.start_button.disabled = True
        self.current_state = None
        if state.state != "down":
            self.current_state = STOP
            self.start_button.disabled = False

    def state_event(self, choised_state):
        if self.current_state is None:
            return
        if choised_state == STOP:
            self.clean_all()
            return
        elif choised_state == PAUSE:
            self._pause_event()
            return
        elif choised_state == START:
            if self.main_mode == AUTO and self.laps == 0:
                return
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

    def _start_event(self):
        # animacion de botones hmi
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

    def clean_all(self):
        if self.main_mode is None:
            return
        # off conteo
        log.info("-------------")
        if self.init_counter:
            self.init_counter = False
            self.sound_claxon = True
            # sonar sirena fin de juego
            log.info("FIN de juego")
        # recupero vueltas seleccionadas
        self.laps = self.backup_laps
        # parametros stop default
        self.current_state = STOP
        "animacion de los botones default"
        for button in self.buttons_id:
            button.disabled = False
        self.start_button.state = "normal"
        self.pause_button.disabled = True
        for mode, button in self.modes.items():
            button.state = "down" if self.main_mode == mode else "normal"
        log.info(f"limpiando en modo {self.main_mode}")
        log.info("-------------")


class gameApp(App):
    def build(self):
        window_setup()
        return viewMain()

    def on_stop(self):
        # Llamar a deinit() explícitamente
        app_widget = self.root
        app_widget.deinit()


if __name__ == "__main__":
    try:
        gameApp().run()
    except Exception as e:
        log.error(f"error de excepcion {e}")
