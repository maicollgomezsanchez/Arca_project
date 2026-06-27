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

class MainScreen(Screen):

    main_mode = None
    label_time_travel = StringProperty("00:10")
    label_time_wait = StringProperty("00:10")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.current_state = "STOP"
        self.clock_event = None

        self.counter_travel = 0
        self.counter_wait = 0

        self.sound_claxon = False

        # hilo bocina
        self.output_bocina = hardware.output_bocina
        self.running_claxon = True
        self.thread_claxon = threading.Thread(target=self.claxon_loop, daemon=True)
        self.thread_claxon.start()

    # -------------------------
    # MODOS
    # -------------------------

    def go_mode(self, mode):
        self.main_mode = mode
        self.ids.left_manager.current = "config"
        self.build_config_screen()

    def go_back(self):
        self.ids.left_manager.current = "modes"

    # -------------------------
    # BOTONES
    # -------------------------

    def start(self):
        if self.current_state == "START":
            return

        self.state_press("START")

    def pause(self):
        self.state_press("PAUSE")

    # -------------------------
    # CONFIG UI
    # -------------------------

    def build_config_screen(self):
        container = self.ids.time_container
        container.clear_widgets()

        def create_display(text_prop, plus_id=None, minus_id=None):
            box = BoxLayout(orientation="vertical")

            lbl = Label(font_size=40)

            def update_label(instance, value):
                lbl.text = value

            self.bind(**{text_prop: update_label})
            lbl.text = getattr(self, text_prop)

            box.add_widget(lbl)

            if plus_id:
                controls = BoxLayout(size_hint_y=0.3)

                btn_plus = Button(text="+")
                btn_minus = Button(text="-")

                btn_plus.bind(
                    on_press=lambda x: self.on_button_press(plus_id),
                    on_release=lambda x: self.on_button_release()
                )
                btn_minus.bind(
                    on_press=lambda x: self.on_button_press(minus_id),
                    on_release=lambda x: self.on_button_release()
                )

                controls.add_widget(btn_plus)
                controls.add_widget(btn_minus)

                box.add_widget(controls)

            return box

        
        lbl_mode = Label(
                text=f"MODO {self.main_mode}",
                font_size=50,
                color=(0, 0, 0, 1),
                size_hint_y=0.3
            )
        container.add_widget(lbl_mode)


        if self.main_mode == "AUTO":
            container.add_widget(create_display("label_time_wait", "auto_+", "auto_-"))
            container.add_widget(create_display("label_time_travel", "travel_+", "travel_-"))

        elif self.main_mode == "SEMI":
            container.add_widget(create_display("label_time_travel", "travel_+", "travel_-"))

        elif self.main_mode == "MANUAL":
            container.add_widget(create_display("label_time_travel"))

    # -------------------------
    # TIEMPOS
    # -------------------------

    def lbl_to_time(self, lbl):
        m, s = map(int, lbl.split(":"))
        return m * 60 + s

    def time_to_lbl(self, t):
        return f"{t//60:02d}:{t%60:02d}"

    # -------------------------
    # CONTROL BOTONES +/-
    # -------------------------

    def set_counters(self, id_button, dt):

        if self.main_mode == "MANUAL":
            return

        timers = {
            "travel_+": ("label_time_travel", 1),
            "travel_-": ("label_time_travel", -1),
            "auto_+": ("label_time_wait", 1),
            "auto_-": ("label_time_wait", -1),
        }

        if id_button not in timers:
            return

        label, inc = timers[id_button]

        t = self.lbl_to_time(getattr(self, label))
        t = max(0, t + inc)

        setattr(self, label, self.time_to_lbl(t))

    def on_button_press(self, button):
        if self.current_state == "STOP":
            self.clock_event_btn = Clock.schedule_interval(
                partial(self.set_counters, button), 0.1
            )

    def on_button_release(self):
        if hasattr(self, "clock_event_btn"):
            self.clock_event_btn.cancel()

    # -------------------------
    # ESTADOS
    # -------------------------

    def state_press(self, state):

        if state == "STOP":
            self.stop_all()
            return

        if state == "START":
            if self.current_state == "STOP":
                self.init_counter()

            elif self.current_state == "PAUSE":
                self.resume()

            return

        if state == "PAUSE":
            self.pause_game()

    # -------------------------
    # LÓGICA ESTADOS
    # -------------------------

    def init_counter(self, dt=None):
        self.current_state = "START"

        if self.main_mode == "MANUAL":
            self.counter_travel = 0
            self.clock_event = Clock.schedule_interval(self.update_manual, 1)

        elif self.main_mode == "SEMI":
            self.counter_travel = self.lbl_to_time(self.label_time_travel)
            self.clock_event = Clock.schedule_interval(self.update_semi, 1)

        elif self.main_mode == "AUTO":
            self.counter_wait = self.lbl_to_time(self.label_time_wait)
            self.clock_event = Clock.schedule_interval(self.update_auto_wait, 1)

    def resume(self):
        self.current_state = "START"

        if self.main_mode == "AUTO":
            self.clock_event = Clock.schedule_interval(self.update_auto_wait, 1)
        else:
            self.clock_event = Clock.schedule_interval(self.update_travel, 1)

    def pause_game(self):
        self.current_state = "PAUSE"
        if self.clock_event:
            self.clock_event.cancel()

        if hardware.output_marcha.is_lit:
            hardware.output_marcha.off()

    def stop_all(self):
        self.current_state = "STOP"

        if self.clock_event:
            self.clock_event.cancel()

        if hardware.output_marcha.is_lit:
            hardware.output_marcha.off()

        self.sound_claxon = True
        self.eating_coin()

    # -------------------------
    # ACTUALIZACIONES
    # -------------------------

    def update_manual(self, dt):
        if self.current_state != "START":
            return

        if not hardware.output_marcha.is_lit:
            hardware.output_marcha.on()

        self.counter_travel += 1
        self.label_time_travel = self.time_to_lbl(self.counter_travel)

    def update_semi(self, dt):
        if self.current_state != "START":
            return

        if not hardware.output_marcha.is_lit:
            hardware.output_marcha.on()

        self.counter_travel -= 1
        self.label_time_travel = self.time_to_lbl(self.counter_travel)

        if self.counter_travel <= 0:
            self.stop_all()

    def update_travel(self, dt):
        self.update_semi(dt)

    def update_auto_wait(self, dt):
        if self.current_state != "START":
            return

        self.counter_wait -= 1
        self.label_time_wait = self.time_to_lbl(self.counter_wait)

        if self.counter_wait <= 0:
            self.sound_claxon = True
            self.clock_event.cancel()
            Clock.schedule_once(self.start_auto_travel, 2)

    def start_auto_travel(self, dt):
        self.counter_travel = self.lbl_to_time(self.label_time_travel)
        self.clock_event = Clock.schedule_interval(self.update_auto_travel, 1)

    def update_auto_travel(self, dt):
        if self.current_state != "START":
            return

        if not hardware.output_marcha.is_lit:
            hardware.output_marcha.on()

        self.counter_travel -= 1
        self.label_time_travel = self.time_to_lbl(self.counter_travel)

        if self.counter_travel <= 0:
            self.sound_claxon = True
            self.clock_event.cancel()
            Clock.schedule_once(self.init_counter, 2)
        
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
            
    # Gestiona los botones especiales como buzzer y moneda
    def special_buttons(self, button_id):
        actions = {
            "buzzer": (self.on_buzzer),
            "coin": (self.eating_coin),
        }

        if button_id in actions:
            action = actions[button_id]
            action()
    # -------------------------
    # BOCINA
    # -------------------------

    def claxon_loop(self):
        while self.running_claxon:
            time.sleep(0.1)
            if self.sound_claxon:
                self.on_buzzer()
                time.sleep(hardware.TIEMPO_DURACION_SIRENA)
                self.off_buzzer()
                self.sound_claxon = False

     # bocina en cualquier momento
    def on_buzzer(self):
        self.output_bocina.on()
        hardware.log.info(f"bocina {self.output_bocina.is_lit}")

    def off_buzzer(self):
        self.output_bocina.off()
        hardware.log.info(f"bocina {self.output_bocina.is_lit}")

    # Maneja la acción de presionar el botón de "decoin"
    def decoin_press(self):
        if self.current_state in ("STOP", None):
            if self.ids.decoin_button.state == "normal":
                self.ids.coin_button.disabled = True
                hardware.log.info("COIN BUTTON BLOCKED")
            else:
                self.ids.coin_button.disabled = False
                
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