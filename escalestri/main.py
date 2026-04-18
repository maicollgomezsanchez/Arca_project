from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import time, threading
import hardware

def window_setup():
    Window.borderless = True
    Window.fullscreen = True
    Window.show_cursor = False
    Window.release_all_keyboards()


class Popup_banner(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):
        self.ids.label_popup.text = new_text


class viewMain(Widget):
    laps = NumericProperty(0)
    backup_laps = NumericProperty(0)

    def init_vars(self):
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
            "mi_label",
            "mi_txt",
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.init_vars()
        self.init_hmi_buts()
        self.output_bocina = hardware.output_bocina
        self.thread_claxon = threading.Thread(target=self.claxon_thread, daemon=True)
        self.thread_claxon.start()
        # funciones de botones externos
        hardware.input_sensor.when_released = self.off_sensor
        hardware.input_sensor.when_pressed = self.on_sensor

        hardware.input_emergency.when_pressed = self.close_popup
        hardware.input_emergency.when_released = self.show_popup

        # inicia funciones de botones remotos
        hardware.input_remote_bocina.when_pressed = self.on_buzzer
        hardware.input_remote_bocina.when_released = self.off_buzzer

        hardware.input_remote_marcha.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self._remote_marcha(), 0
        )
        hardware.input_remote_pausa.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self._remote_pausa(), 0
        )
        hardware.input_remote_paro.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self._remote_paro(), 0
        )
        hardware.output_luces.on()
        hardware.log.info("luces on!")

    def deinit(self):
        self.running = False
        try:
            self.thread_claxon.join()
            hardware.log.info("Hilos detenidos correctamente")
        except Exception as e:
            hardware.log.error(f"Error al detener los hilos: {e}")
        finally:
            hardware.close_all_pins()
            hardware.log.info("Pines cerrados correctamente")

    # funciones de botones externos
    def on_buzzer(self):
        self.output_bocina.on()
        hardware.log.info("bocina on!")

    def off_buzzer(self):
        self.output_bocina.off()
        hardware.log.info("bocina off!")

    def on_sensor(self):
        if not self.sensor_pressed:
            self.sensor_pressed = True

            if not self.init_counter:
                return
            # cambia la variable cuando presiona el boton
            mode_delta = {hardware.MANUAL: 1, hardware.AUTO: -1}
            delta = mode_delta.get(self.main_mode, 0)

            if delta != 0:
                self.laps = max(0, self.laps + delta)
                hardware.log.debug(f"Modo {self.main_mode}, vueltas: {self.laps}")
            # cerrar si llega a limites
            limit_manual = self.main_mode == hardware.MANUAL and self.laps == hardware.MAXIMAS_VUELTAS
            limit_auto = self.main_mode == hardware.AUTO and self.laps == 0

            if limit_auto or limit_manual:
                self.clean_all()

    def off_sensor(self):
        if self.sensor_pressed:
            self.sensor_pressed = False

    def _remote_marcha(self):
        hardware.log.warning("marcha por remoto")
        self.state_press(hardware.START)

    def _remote_paro(self):
        hardware.log.warning("paro por remoto")
        self.state_press(hardware.STOP)

    def _remote_pausa(self):
        hardware.log.warning("pausa por remoto")
        self.state_press(hardware.PAUSE)

    # funciones de  pop up
    def show_popup(self):
        if not self.popup_enabled:
            self.popup_enabled = True
            self.init_counter = False
            self.off_buzzer()
            self.clean_all()
            hardware.log.info("SIRENA EMERGENCIA !!!")
            Clock.schedule_once(self._open_popup, 0)

    def close_popup(self):
        if self.popup_enabled:
            self.popup_enabled = False
            self.current_state = hardware.STOP
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
        hardware.log.info("iniciando hilo de sirena")
        while self.running:
            time.sleep(0.1)
            try:
                if self.sound_claxon:
                    self.on_buzzer()
                    hardware.log.info("sonando Bocina !!!")
                    time.sleep(hardware.TIEMPO_DURACION_SIRENA)
                    self.off_buzzer()
                    self.sound_claxon = False

            except Exception as e:
                hardware.log.error(f"Error en claxon_thread: {e}")
                self.off_buzzer()

    # funciones HMI
    def init_hmi_buts(self):
        for ids in self.buttons_name:
            setattr(self, ids, self.ids[ids])
        self.buttons = [self.manual_button, self.auto_button, self.start_button, self.pause_button]
        self.modes = {
            hardware.AUTO: self.auto_button,
            hardware.MANUAL: self.manual_button,
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

        if self.current_state == hardware.STOP and self.continuous_event:
            self.continuous_event.cancel()
            self.backup_laps = self.laps
            hardware.log.info(f"vueltas definidas: {self.laps}")

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
                    self.state_press(hardware.STOP)
                    return super().on_touch_down(touch)

                if self.current_state in (hardware.STOP, None):
                    if widget_id == "manual_button" and self.main_mode is not hardware.MANUAL:
                        self.mode_press(hardware.MANUAL, btn)
                        return super().on_touch_down(touch)

                    if widget_id == "auto_button" and self.main_mode is not hardware.AUTO:
                        self.mode_press(hardware.AUTO, btn)
                        return super().on_touch_down(touch)

                if self.current_state is hardware.STOP:
                    if widget_id in ("mayor_button", "minus_button"):
                        self.on_button_press(widget_id)
                        return super().on_touch_down(touch)

                if self.current_state in (hardware.STOP, hardware.PAUSE):
                    if widget_id == "start_button":
                        self.state_press(hardware.START)
                        return super().on_touch_down(touch)

                if self.current_state is hardware.START:
                    if widget_id == "pause_button":
                        self.state_press(hardware.PAUSE)
                        return super().on_touch_down(touch)
        return False

    def set_timers(self, id_button, dt):
        timers = {
            "mayor_button": 1,
            "minus_button": -1,
        }
        if id_button in timers:
            increment = timers[id_button]
            self.laps = max(0, min(hardware.MAXIMAS_VUELTAS, self.laps + increment))

    def on_button_press(self, button):
        self.continuous_event = None
        if self.current_state == hardware.STOP and self.main_mode == hardware.AUTO:
            self.continuous_event = Clock.schedule_interval(
                partial(self.set_timers, button), 0.1
            )

    def mode_press(self, mode_select, mode_state):
        self.backup_laps = self.laps
        self.main_mode = mode_select
        self.current_state = None
        hardware.log.info(f"main_mode: {self.main_mode}")
        if mode_state != "down":
            self.current_state = hardware.STOP
            if self.main_mode == hardware.MANUAL:
                self.laps = 0

    def state_press(self, choised_state):
        if self.current_state is None:
            return
        if choised_state == hardware.STOP:
            self.clean_all()
            return
        elif choised_state == hardware.PAUSE:
            self._pause_event()
            return
        elif choised_state == hardware.START:
            if self.main_mode == hardware.AUTO and self.laps == 0:
                return
            self._start_event()
            return

    def _pause_event(self):
        self.mi_label.color = ('#ff8000')
        self.mi_txt.color = self.mi_label.color
        # animicacion de botones HMI pausa
        self.start_button.disabled = False
        self.pause_button.disabled = True
        hardware.log.info("En Pausa")
        self.current_state = hardware.PAUSE
        self.init_counter = False
        hardware.output_marcha.off()
        hardware.log.info("Marcha Off")
        time.sleep(hardware.TIEMPO_RETARDO_LUCES)
        hardware.output_luces.on()
        hardware.log.info("luces on!!!")

    def _start_event(self):
        # animacion de botones hmi
        self.mi_label.color = ("#00aa00")
        self.mi_txt.color = self.mi_label.color
        self.manual_button.disabled = True
        self.auto_button.disabled = True
        self.start_button.disabled = True
        self.pause_button.disabled = False
        hardware.log.info(
            "Iniciar evento" if self.current_state == hardware.STOP else "Re-iniciar evento"
        )
        if self.current_state == hardware.STOP:
            # activa sirena de inicio
            self.sound_claxon = True
            # guarda las vueltas seleccionadas
            self.backup_laps = self.laps
            # actualiza la vueltas en la HMI
            self.laps = self.backup_laps if self.main_mode == hardware.AUTO else 0
        
        while self.sound_claxon:
            time.sleep(hardware.TIEMPO_REBOTE_SENSOR)

        self.current_state = hardware.START
        self.init_counter = True
        hardware.output_luces.off()
        hardware.log.info("luces off")
        time.sleep(hardware.TIEMPO_RETARDO_LUCES)
        hardware.output_marcha.on()
        hardware.log.info("Marcha On!!!")

    def clean_all(self):
        if self.main_mode is None:
            return
        # off conteo
        self.mi_label.color = (0,0,0,1)
        self.mi_txt.color = self.mi_label.color
        hardware.log.info("-------------")
        if self.init_counter:
            self.init_counter = False
            self.sound_claxon = True
            # sonar sirena fin de juego
            hardware.log.info("FIN de juego")
        # recupero vueltas seleccionadas
        self.laps = self.backup_laps
        # parametros stop default
        self.current_state = hardware.STOP
        hardware.output_marcha.off()
        hardware.log.info("Marcha Off")
        time.sleep(hardware.TIEMPO_RETARDO_LUCES)
        hardware.output_luces.on()
        hardware.log.info("luces on!")
        "animacion de los botones default"
        for button in self.buttons:
            button.disabled = False
        for mode, button in self.modes.items():
            button.state = "down" if self.main_mode == mode else "normal"
        #hardware.log.info(f"limpiando en modo {self.main_mode}")


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
    except Exception as e:
        hardware.log.error(f"error de excepcion {e}")
    except KeyboardInterrupt:
        hardware.log.error("keyboard exit")
    finally:
        hardware.close_all_pins()

