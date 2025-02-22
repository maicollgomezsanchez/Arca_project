from gpiozero import Device
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import LED, Button
from time import sleep
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from threading import Thread
from kivy.uix.widget import Widget

Device.pin_factory = PiGPIOFactory()

PIN_EMERGENCY = 2
PIN_SENSOR = 3
PIN_MARCHA = 4
PIN_BOCINA = 17

def check_pin_free(pin):
    try:
        test_led = LED(pin)
        test_led.close()
        return True
    except Exception as e:
        print(f"Error al acceder al pin {pin}: {e}")
        return False

if not all([check_pin_free(PIN_BOCINA), check_pin_free(PIN_MARCHA), check_pin_free(PIN_SENSOR), check_pin_free(PIN_EMERGENCY)]):
    print("Uno o más pines están ocupados. No puedo iniciar la aplicación.")
else:
    output_bocina = LED(PIN_BOCINA)
    output_marcha = LED(PIN_MARCHA)
    input_sensor = Button(PIN_SENSOR, pull_up=True)
    input_emergency = Button(PIN_EMERGENCY, pull_up=True)

    color_fondo_pantalla = '#cee5e5'  # Color de fondo

    # Clase para el fondo con color
    class BackgroundWidget(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.color = get_color_from_hex(color_fondo_pantalla)  # Obtener el color del fondo

        def on_size(self, *args):
            # Redibujar el fondo cuando cambie el tamaño de la pantalla
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*self.color)  # Aplicar el color de fondo
                self.rect = Rectangle(size=self.size, pos=self.pos)

        def on_pos(self, *args):
            # Redibujar el fondo cuando cambie la posición
            self.canvas.before.clear()
            with self.canvas.before:
                Color(*self.color)
                self.rect = Rectangle(size=self.size, pos=self.pos)

    class GPIOApp(App):
        def build(self):
            # Asegúrate de que el layout ocupe todo el tamaño de la pantalla

            # Añadir fondo
            self.layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
            self.layout = BackgroundWidget(orientation='vertical', size_hint=(1, 1))

            # Etiquetas
            self.label_sensor = Label(text="Sensor: No presionado", color=(0, 0, 0, 1))
            self.label_emergency = Label(text="Emergencia: No activada", color=(0, 0, 0, 1))
            
            # Botones ToggleButton con tamaño ajustable
            self.btn_marcha = ToggleButton(text="Encender Marcha", on_press=self.toggle_marcha, size_hint=(1, None), height=50, color=(0, 0, 0, 1))
            self.btn_bocina = ToggleButton(text="Encender Bocina", on_press=self.toggle_bocina, size_hint=(1, None), height=50, color=(0, 0, 0, 1))
            
            # Añadir widgets al layout
            self.layout.add_widget(self.label_sensor)
            self.layout.add_widget(self.label_emergency)
            self.layout.add_widget(self.btn_marcha)
            self.layout.add_widget(self.btn_bocina)
            
            self.update_thread = Thread(target=self.update_labels, daemon=True)
            self.update_thread.start()

            return self.layout
        
        def toggle_marcha(self, instance):
            if instance.state == 'down':
                output_marcha.on()
                instance.text = "Apagar Marcha"
            else:
                output_marcha.off()
                instance.text = "Encender Marcha"
        
        def toggle_bocina(self, instance):
            if instance.state == 'down':
                output_bocina.on()
                instance.text = "Apagar Bocina"
            else:
                output_bocina.off()
                instance.text = "Encender Bocina"
        
        def update_labels(self):
            while True:
                self.label_sensor.text = "Sensor: Presionado" if input_sensor.is_pressed else "Sensor: No presionado"
                self.label_emergency.text = "Emergencia: Activada" if not input_emergency.is_pressed else "Emergencia: No activada"
                sleep(0.1)

    if __name__ == "__main__":
        try:
            GPIOApp().run()
        except KeyboardInterrupt:
            print("Interrupción por teclado")
            output_marcha.off()
            output_bocina.off()
        finally:
            input_emergency.close()
            input_sensor.close()
            output_bocina.close()
            output_marcha.close()
            print("FIN")
