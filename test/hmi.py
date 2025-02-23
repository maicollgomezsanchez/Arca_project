from time import sleep
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from hardware import (
    output_marcha,
    output_bocina,
    input_emergency,
    input_sensor,
    close_all_pins,
)


color_fondo_pantalla = "#cee5e5"  # Color de fondo


# Clase para el fondo con color
class BackgroundWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = get_color_from_hex(
            color_fondo_pantalla
        )  # Obtener el color del fondo

    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.color)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def on_pos(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.color)
            self.rect = Rectangle(size=self.size, pos=self.pos)


class GPIOApp(App):
    def build(self):

        self.layout = BoxLayout(orientation="vertical", size_hint=(1, 1))
        self.layout = BackgroundWidget(orientation="vertical", size_hint=(1, 1))

        self.label_sensor = Label(text="Sensor: No presionado", color=(0, 0, 0, 1))
        self.label_emergency = Label(text="Emergencia: No activada", color=(0, 0, 0, 1))

        self.btn_marcha = ToggleButton(
            text="Encender Marcha",
            on_press=self.toggle_marcha,
            size_hint=(1, None),
            height=50,
            color=(0, 0, 0, 1),
        )
        self.btn_bocina = ToggleButton(
            text="Encender Bocina",
            on_press=self.toggle_bocina,
            size_hint=(1, None),
            height=50,
            color=(0, 0, 0, 1),
        )

        self.layout.add_widget(self.label_sensor)
        self.layout.add_widget(self.label_emergency)
        self.layout.add_widget(self.btn_marcha)
        self.layout.add_widget(self.btn_bocina)

        input_sensor.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self.label_sensor_active(), 0
        )
        input_sensor.when_released = lambda: Clock.schedule_once(
            lambda dt: self.label_sensor_deactive(), 0
        )
        input_emergency.when_pressed = lambda: Clock.schedule_once(
            lambda dt: self.label_emergency_active(), 0
        )
        input_emergency.when_released = lambda: Clock.schedule_once(
            lambda dt: self.label_emergency_deactive(), 0
        )

        return self.layout

    def label_emergency_active(self):
        self.label_emergency.text("Emergencia: Activada")

    def label_emergency_deactive(self):
        self.label_emergency.text("Emergencia: No activada")

    def label_sensor_active(self):
        self.label_sensor.text("Sensor: Presionado")

    def label_sensor_deactive(self):
        self.label_sensor.text("Sensor: No presionado")

    def toggle_marcha(self, instance):
        if instance.state == "down":
            output_marcha.on()
            instance.text = "Apagar Marcha"
        else:
            output_marcha.off()
            instance.text = "Encender Marcha"

    def toggle_bocina(self, instance):
        if instance.state == "down":
            output_bocina.on()
            instance.text = "Apagar Bocina"
        else:
            output_bocina.off()
            instance.text = "Encender Bocina"


if __name__ == "__main__":
    try:
        GPIOApp().run()
    except KeyboardInterrupt:
        print("Interrupción por teclado")
        output_marcha.off()
        output_bocina.off()
    finally:
        close_all_pins()
        print("FIN")
