from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

class ViewMain(BoxLayout):
    def mode_press(self, button, touch):
        """ Maneja la selección del modo cuando el usuario suelta el botón """
        if button.collide_point(*touch.pos):
            self.reset_modes()
            button.state = 'down'  # Activa el botón seleccionado
            print(f"Modo seleccionado: {button.text}")

    def reset_modes(self):
        """ Restaura todos los modos a su estado 'normal' """
        self.ids.manual_button.state = 'normal'
        self.ids.semi_button.state = 'normal'
        self.ids.auto_button.state = 'normal'

class MainApp(App):
    def build(self):
        return ViewMain()

if __name__ == '__main__':
    MainApp().run()
