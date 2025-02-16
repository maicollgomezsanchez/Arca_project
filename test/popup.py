from gpiozero import Button
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.button import Button as KivyButton

# Definir el botón físico en el GPIO 3 (puedes cambiarlo)
GPIO_PIN = 3
input_sensor = Button(GPIO_PIN, pull_up=True)

class GPIOApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        # Botón en la interfaz gráfica
        self.btn_marcha = KivyButton(
            text="Esperando entrada...",
            size_hint=(None, None),
            size=(200, 50)
        )

        self.layout.add_widget(self.btn_marcha)

        # Crear una variable para el popup
        self.popup = None

        # Configurar la detección del botón físico
        input_sensor.when_pressed = self.show_popup
        input_sensor.when_released = self.close_popup

        return self.layout

    def show_popup(self):
        """ Muestra el popup en el hilo principal de Kivy. """
        Clock.schedule_once(self._open_popup, 0)

    def _open_popup(self, dt):
        """ Lógica para abrir el popup. """
        popup_content = BoxLayout(orientation='vertical')
        popup_label = Label(text="¡Entrada detectada!")
        popup_content.add_widget(popup_label)

        self.popup = Popup(title="Alerta", content=popup_content, size_hint=(None, None), size=(400, 200))
        self.popup.open()

        # Cambia el texto del botón
        self.btn_marcha.text = "¡Entrada activa!"

    def close_popup(self):
        """ Cierra el popup cuando se libera el botón físico. """
        Clock.schedule_once(self._dismiss_popup, 0)

    def _dismiss_popup(self, dt):
        """ Lógica para cerrar el popup. """
        if self.popup:
            self.popup.dismiss()
            self.popup = None

        # Restablecer el texto del botón
        self.btn_marcha.text = "Esperando entrada..."

if __name__ == "__main__":
    GPIOApp().run()