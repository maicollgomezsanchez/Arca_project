#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial

TIEMPO_SIRENA = 3  # Tiempo de duración de la sirena en segundos


class GPIO_raspi:
    def __init__(self):
        pass

    def enable_pin():
        pass


class Popup_banner(Popup):  # Clase para la ventana emergente (popup)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_text(self, new_text):  # Establece el texto que se muestra en el popup
        self.ids.label_popup.text = new_text


class viewMain(Widget):  # Clase principal que maneja la interfaz y la lógica del juego
    # Variables de estado y botones
    main_mode = None
    current_state = None
    label_time_travel = ObjectProperty("00:05")  # Tiempo de viaje (viaje)
    label_time_wait = ObjectProperty("00:05")  # Tiempo automático
    clock_event = None  # Evento de reloj para actualizar el tiempo
    counter_travel = 0  # Contador de tiempo de viaje
    counter_wait = 0  # Contador de tiempo de espera
    popup = None  # Variable para manejar el popup
    current_game = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_buttons()

    # Inicializa los botones de la interfaz
    def init_buttons(self):
        try:
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

        except Exception as e:
            print(e)

    # Configura los tiempos de respaldo
    def setup_time(self):
        try:
            self.backup_label_auto = self.label_time_wait
            self.backup_label_travel = self.label_time_travel

        except Exception as e:
            print(e)

    # Convierte el formato de tiempo de etiqueta a segundos
    def lbl_to_time(self, lbl: str) -> int:
        try:
            mins, secs = map(int, lbl.split(":"))
            return mins * 60 + secs

        except Exception as e:
            print(e)

    # Convierte el tiempo en segundos a formato de etiqueta (mm:ss)
    def time_to_lbl(self, time):
        try:
            return f"{time // 60:02d}:{time % 60:02d}"

        except Exception as e:
            print(e)

    # Activa la bocina
    def power_buzzer(self):
        try:
            print("BUZZZZZ !!!!!")

        except Exception as e:
            print(e)

    # Simula el consumo de una moneda
    def eating_coin(self):
        try:
            print("COMIENDO FICHAS !!!")

        except Exception as e:
            print(e)

    # Gestiona los botones especiales como buzzer y moneda
    def special_buttons(self, button_id):
        try:
            actions = {
                "buzzer": ("bocina!", self.power_buzzer),
                "coin": ("comiendo ficha!", self.eating_coin),
            }

            if button_id in actions:
                action = actions[button_id]
                #self.enable_popup(text, 0.3)
                action()

        except Exception as e:
            print(e)

    # Ajusta los temporizadores según el botón presionado

    def set_timers(self, id_button, dt):
        try:
            timers = {
                "travel_+": ("label_time_travel", 1),
                "travel_-": ("label_time_travel", -1),
                "auto_+": ("label_time_wait", 1),
                "auto_-": ("label_time_wait", -1),
            }

            if id_button in timers:
                label, increment = timers[id_button]
                current_time = self.lbl_to_time(getattr(self, label))
                new_time = max(0, current_time + increment)
                setattr(self, label, self.time_to_lbl(new_time))

        except Exception as e:
            print(e)

    # Función llamada al presionar un botón
    def on_button_press(self, button):
        try:
            if self.current_state == "STOP":
                self.continuous_event = Clock.schedule_interval(
                    partial(self.set_timers, button), 0.1
                )

        except Exception as e:
            print(e)

    # Función llamada al soltar un botón
    def on_button_release(self):
        try:
            if self.current_state == "STOP" and self.continuous_event:
                self.continuous_event.cancel()
                self.setup_time()

        except Exception as e:
            print(e)

    # Maneja la acción de presionar el botón de "decoin"
    def decoin_press(self):
        try:
            if self.current_state in ("STOP", None):
                if self.decoin_button.state == "normal":
                    self.coin_button.disabled = True
                    #self.enable_popup("bloqueo de descarga !", 0.5)
                    print("bloqueando boton de comer fichas")

                else:
                    self.coin_button.disabled = False
                    #self.enable_popup("activando descarga !", 0.5)
                    print("boton de comer fichas activado")

        except Exception as e:
            print(e)

    # Cambia el modo de operación
    def mode_press(self, mode_select, mode_state):
        try:
            self.setup_time()
            self.main_mode = mode_select
            self.current_state = "STOP"
            self.pause_button.disabled = True
            self.start_button.disabled = True

            if mode_state == "down":
                self.start_button.disabled = False

        except Exception as e:
            print(e)

    # Cambia el estado del sistema
    def state_press(self, state_select, state_value):
        try:
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
                    return

                if self.current_state == "PAUSE":
                    self.current_state = "START"

                    if self.main_mode == "AUTO":
                        self.clock_event = Clock.schedule_interval(
                            self.update_wait_time, 1
                        )
                        return

                    self.clock_event = Clock.schedule_interval(
                        self.update_travel_time, 1
                    )
                    return

            if state_select == "PAUSE":
                print(f"pausado en modo: {self.main_mode}")
                self.start_button.disabled = False
                self.pause_button.disabled = True
                self.pause_button.state = "normal"
                self.current_state = "PAUSE"
                Clock.unschedule(self.clock_event)
                return

            raise ValueError("error states")

        except Exception as e:
            print(e)

    # Inicializa los contadores de tiempo
    def init_counter(self):
        try:
            if self.current_state == "STOP":
                self.current_state = "START"
                self.counter_travel = -TIEMPO_SIRENA
                self.counter_wait = 0
                self.current_game = True
                self.active_sound = True
                self.label_time_wait = "00:00"
                self.label_time_travel = "00:00"
                self.timeout_travel = self.lbl_to_time(self.backup_label_travel)

                if self.main_mode == "AUTO":
                    self.timeout_wait = self.lbl_to_time(self.backup_label_auto)
                    self.label_time_travel = f"{self.backup_label_travel}/00:00"
                    self.label_time_wait = f"{self.backup_label_auto}/00:00"
                    print("conteo de espera modo AUTO")
                    self.clock_event = Clock.schedule_interval(self.update_wait_time, 1)
                    return

                elif self.main_mode in {"MANUAL", "SEMI"}:
                    if self.main_mode == "SEMI":
                        self.label_time_travel = f"{self.backup_label_travel}/00:00"

                    self.clock_event = Clock.schedule_interval(
                        self.update_travel_time, 1
                    )
                    return

            raise ValueError("error init_counter")

        except Exception as e:
            print(e)

    # Actualiza el tiempo de espera
    def update_wait_time(self, dt):
        try:
            if self.current_state == "START":
                self.counter_wait += 1

                if self.counter_wait > self.timeout_wait:
                    print("finaliza espera modo AUTO")
                    self.clock_event.cancel()
                    self.clock_event = Clock.schedule_interval(
                        self.update_travel_time, 1
                    )

                else:
                    self.label_time_wait = f"{self.backup_label_auto}/{self.time_to_lbl(self.counter_wait)}"

        except Exception as e:
            print(e)

    # Actualiza el tiempo de viaje
    def update_travel_time(self, dt):
        try:
            if self.current_state == "START":
                self.counter_travel += 1

                if self.active_sound == True:
                    self.active_sound = False
                    print(f"comienza el juego en {self.main_mode}")
                    #self.enable_popup("comienza el juego !!!", TIEMPO_SIRENA)
                    self.power_buzzer()

                if self.counter_travel > 0:
                    if self.main_mode == "MANUAL":
                        self.label_time_travel = self.time_to_lbl(self.counter_travel)

                    else:
                        self.label_time_travel = f"{self.backup_label_travel}/{self.time_to_lbl(self.counter_travel)}"

                if (
                    self.main_mode != "MANUAL"
                    and self.counter_travel > self.timeout_travel
                ):

                    if self.main_mode == "SEMI":
                        print("finaliza en semi")
                        self.clean_all()

                    elif self.main_mode == "AUTO":
                        # descarga automatica, si boton presionado
                        if self.decoin_button.state == "down":
                            self.eating_coin()

                        self.clock_event.cancel()
                        self.current_state = "STOP"
                        #self.enable_popup("se acabó !", 0.5)
                        self.power_buzzer()
                        print("finaliza en auto")
                        self.init_counter()

        except Exception as e:
            print(e)

    # Limpia todos los estados y reinicia los temporizadores
    def clean_all(self):
        try:
            if self.main_mode is not None and self.current_game is True:
                #self.enable_popup("se acabó !!!", 0.5)
                self.eating_coin() # comer fichas
                self.power_buzzer()
                self.current_game = False

            Clock.unschedule(self.clock_event)
            self.current_state = "STOP"

            self.manual_button.disabled = False
            self.semi_button.disabled = False
            self.auto_button.disabled = False

            self.start_button.disabled = False
            self.start_button.state = "normal"

            self.pause_button.disabled = True

            if self.decoin_button.state == "down":
                self.coin_button.disabled = False

            self.label_time_wait = self.backup_label_auto
            self.label_time_travel = self.backup_label_travel
            # manejo de modo actual
            if self.main_mode == "AUTO":
                self.auto_button.state = "down"
                self.manual_button.state = "normal"
                self.semi_button.state = "normal"

            elif self.main_mode == "MANUAL":
                self.auto_button.state = "normal"
                self.manual_button.state = "down"
                self.semi_button.state = "normal"

            elif self.main_mode == "SEMI":
                self.auto_button.state = "normal"
                self.manual_button.state = "normal"
                self.semi_button.state = "down"

        except Exception as e:
            print(e)

    # Manejo de popups
    def enable_popup(self, text: str, delay):
        self.open_popup(text)
        self.close_popup_after_delay(delay)

    # Muestra un popup con el texto dado
    def open_popup(self, text: str):
        try:
            if not self.popup:
                self.popup = Popup_banner()

            self.popup.setup_text(text)
            self.popup.open()

        except Exception as e:
            print(e)

    # Cierra el popup después de un retraso
    def close_popup_after_delay(self, delay):
        Clock.schedule_once(self.close_popup, delay)

    # Cierra el popup
    def close_popup(self, dt):
        if self.popup:
            self.popup.dismiss()
            self.popup = None


# Clase principal de la aplicación Kivy
class babylandiaApp(App):
    def build(self):
        # Configura la ventana sin bordes
        Window.borderless = False
        # Descomentar para pantalla completa
        Window.fullscreen = False
        return viewMain()


# Ejecuta la aplicación
if __name__ == "__main__":
    babylandiaApp().run()
