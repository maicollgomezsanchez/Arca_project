from kivy.app import App
from kivy.uix.widget import Widget

class MyWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Inicialización de recursos
        print("Widget creado")

    def deinit(self):
        # Limpieza de recursos
        print("Widget destruido y recursos liberados")
    
    def on_touch_down(self, touch):
        print("Tocando widget")

class MyApp(App):
    def build(self):
        return MyWidget()

    def on_stop(self):
        # Llamar a deinit() explícitamente
        app_widget = self.root
        app_widget.deinit()

if __name__ == "__main__":
    MyApp().run()