from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
import time, threading
import hardware


from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


        
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

#class viewMain(Widget):  # Clase principal que maneja la interfaz y la lógica del juego
class MainScreen(Screen):
    # Variables de estado y botones
    main_mode = None
    current_state = None
    label_time_travel = StringProperty("00:10")  # Tiempo de viaje
    label_time_wait = StringProperty("00:10")  # Tiempo automático
    clock_event = None  # Evento de reloj para actualizar el tiempo
    counter_travel = 0  # Contador de tiempo de viaje
    counter_wait = 0  # Contador de tiempo de espera
    popup = None  # Variable para manejar el popup
    current_game = None
    running_claxon = True
    sound_claxon = False
    
    def go_mode(self, mode):
        self.main_mode = mode

        self.ids.left_manager.current = "config"
        self.build_config_screen()
    
    def go_back(self):
        self.ids.left_manager.current = "modes"
        
        
    def start(self):
        self.state_press("START", "down")

    def pause(self):
        self.state_press("PAUSE", "down")

    def build_config_screen(self):
        container = self.ids.time_container
        container.clear_widgets()

        def create_display(text_prop, plus_id, minus_id):
            box = BoxLayout(orientation="vertical")

            lbl = Label(font_size=40)
            lbl.bind(text=lambda instance, value: None)  # dummy (evita warnings)

            def update_label(*args):
                lbl.text = getattr(self, text_prop)

            update_label()
            self.bind(**{text_prop: lambda instance, value: update_label()})

            controls = BoxLayout(size_hint_y=0.3)

            btn_plus = Button(text="+")
            btn_minus = Button(text="-")

            btn_plus.bind(on_press=lambda x: self.on_button_press(plus_id))
            btn_minus.bind(on_press=lambda x: self.on_button_press(minus_id))

            controls.add_widget(btn_plus)
            controls.add_widget(btn_minus)

            box.add_widget(lbl)
            box.add_widget(controls)

            return box

        if self.main_mode == "AUTO":
            container.add_widget(
                create_display("label_time_wait", "auto_+", "auto_-")
            )
            container.add_widget(
                create_display("label_time_travel", "travel_+", "travel_-")
            )

        elif self.main_mode == "SEMI":
            container.add_widget(
                create_display("label_time_travel", "travel_+", "travel_-")
            )


    def deinit(self):
        self.running = False
        try:
            self.claxon_loop.join(timeout=1)
            hardware.log.info("Hilos detenidos correctamente")
        except Exception as e:
            hardware.log.error(f"Error al detener los hilos: {e}")
        finally:
            hardware.close_all_pins()
    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.continuous_event = None
        self.output_bocina = hardware.output_bocina
        self.thread_buzzer = None
        self.thread_coin = None
        #hilo de bocina
        self.thread_claxon = threading.Thread(target=self.claxon_loop, daemon=True)
        if not self.thread_claxon.is_alive():
            self.thread_claxon.start()
        
        #hardware.input_emergency.when_pressed = self.close_popup
        #hardware.input_emergency.when_released = self.show_popup        

 # bocina en cualquier momento
    def on_buzzer(self):
        self.output_bocina.on()
        hardware.log.info(f"bocina {self.output_bocina.is_lit}")

    def off_buzzer(self):
        self.output_bocina.off()
        hardware.log.info(f"bocina {self.output_bocina.is_lit}")
        
    def claxon_loop(self):
        hardware.log.info("iniciando hilo de bocina")
        while self.running_claxon:
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

    # consumo de una moneda
    def eating_coin(self):
        self.pulse_count = 0
        self.pulse_on = False
        self.coin_event = Clock.schedule_interval(self._coin_pulse_cycle, hardware.TIEMPO_PULSOS_FICHA)
    
    def _coin_pulse_cycle(self, dt):
        if not self.pulse_on:
            hardware.output_traga_ficha.on()
            self.pulse_on = True
            hardware.log.info(f"comiendo ficha x {self.pulse_count + 1} vez")
        else:
            hardware.output_traga_ficha.off()
            self.pulse_on = False
            self.pulse_count += 1
            # Cuando termina el OFF contamos un pulso completo
            if self.pulse_count >= hardware.MAXIMO_PULSOS_FICHA:
                self.coin_event.cancel()

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
            "buzzer": (self.on_buzzer),
            "coin": (self.eating_coin),
        }

        if button_id in actions:
            action = actions[button_id]
            action()

    # Maneja la acción de presionar el botón de "decoin"
    def decoin_press(self):
        if self.current_state in ("STOP", None):
            if self.ids.decoin_button.state == "normal":
                self.ids.coin_button.disabled = True
                hardware.log.info("COIN BUTTON BLOCKED")
            else:
                self.ids.coin_button.disabled = False

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
                current_time = min(hardware.TIEMPO_MAXIMO_ESPERA, new_time)

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

    # Cambia el modo de operación
    def mode_press(self, mode_select, mode_state):
        self.setup_time()
        self.main_mode = mode_select
        self.current_state = "STOP"


    # Cambia el estado del sistema
    def state_press(self, state_select, state_value):
        if self.current_state is None:
            return

        if state_select == "STOP":
            self.clean_all()
            return

        if state_select == "START":
            self.ids.coin_button.disabled = True

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
            hardware.log.info(f"pausado en modo: {self.main_mode}")
            #apagando marcha si esta encendido
            if hardware.output_marcha.is_lit:
                hardware.output_marcha.off()
                hardware.log.info(f"marcha {hardware.output_marcha.is_lit}")
            self.current_state = "PAUSE"
            if self.clock_event:
                self.clock_event.cancel()
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
            hardware.log.info("Conteo de espera en modo AUTO")
            self.clock_event = Clock.schedule_interval(self.update_wait_time, 1)
            return

        self.sound_claxon = True
        Clock.schedule_once(self.start_travel_after_buzzer, 2)

    def start_travel_after_buzzer(self, dt):
        hardware.log.info(f"Comienza el juego en {self.main_mode}")
        self.clock_event = Clock.schedule_interval(self.update_travel_time, 1)

    # Actualiza el tiempo de espera (decrece)
    def update_wait_time(self, dt):
        if self.current_state == "START":
            self.counter_wait = self.counter_wait - 1
            self.label_time_wait = self.time_to_lbl(self.counter_wait)
            if self.counter_wait <= 0:
                # hace sonar la bocina por dos segundos y espera
                hardware.log.info("Finaliza espera en modo AUTO inicia temporizador")
                self.sound_claxon = True
                self.clock_event.cancel()
                Clock.schedule_once(self.stop_claxon_and_continue, 2)

    def stop_claxon_and_continue(self, dt):
        self.clock_event = Clock.schedule_interval(self.update_travel_time, 1)
        
    # Actualiza el tiempo de viaje
    def update_travel_time(self, dt):
        if self.current_state != "START":
            return
        # se enciende la salida de marcha y si se apaga por algo se vuelve a encender
        if not hardware.output_marcha.is_lit:
            hardware.output_marcha.on()
            hardware.log.info(f"marcha {hardware.output_marcha.is_lit}")
            
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
            hardware.log.info(f"Finaliza en {self.main_mode}")
            if self.main_mode == "SEMI":
                self.clean_all()

            elif self.main_mode == "AUTO":
                if self.ids.decoin_button.state == "down":
                    self.eating_coin()

                self.clock_event.cancel()
                self.current_state = "STOP"
                #suena bocina
                self.sound_claxon = True
                # Programar continuacion en 2 segundos
                Clock.schedule_once(self.stop_claxon_and_init, 2)

    def stop_claxon_and_init(self, dt):
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
        #Clock.unschedule(self.clock_event)
        if self.clock_event:
            self.clock_event.cancel()
        self.current_state = "STOP"
        # apaga la marcha
        #apagando marcha si esta encendido
        if hardware.output_marcha.is_lit:
            hardware.output_marcha.off()
            hardware.log.info(f"marcha {hardware.output_marcha.is_lit}")

        # Habilitar botones
        '''for button in [
            self.manual_button,
            self.semi_button,
            self.auto_button,
            self.start_button,
        ]:
            button.disabled = False'''

        #self.start_button.state = "normal"
        #self.pause_button.disabled = True

        if self.decoin_button.state == "down":
            self.coin_button.disabled = False

        # Configurar estado de botones según el modo
        '''modes = {
            "AUTO": self.auto_button,
            "MANUAL": self.manual_button,
            "SEMI": self.semi_button,
        }
        for mode, button in modes.items():
            button.state = "down" if self.main_mode == mode else "normal"'''
        hardware.log.info(f"limpiando en modo {self.main_mode}")
        # Acciones finales si el juego estaba activo
        if self.current_game:
            self.eating_coin()
            self.on_buzzer()
            self.current_game = False

    # funciones de  pop up
    def show_popup(self, dt):
        if self.clock_event:
            self.clock_event.cancel()
        hardware.log.warning("Emergencia presionada")
        self.on_buzzer()
        Clock.schedule_once(self._open_popup, 0)

    def close_popup(self, dt):
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