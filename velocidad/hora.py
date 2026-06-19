import os
import calendar
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.label import Label


class DateTimePopup(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)

        now = datetime.now()

        # Año
        self.year_spinner = Spinner(
            text=str(now.year),
            values=[str(y) for y in range(2020, 2035)],
            size_hint=(1, 0.2)
        )

        # Mes
        self.month_spinner = Spinner(
            text=str(now.month),
            values=[str(m) for m in range(1, 13)],
            size_hint=(1, 0.2)
        )
        self.month_spinner.bind(text=self.update_days)

        # Día
        self.day_spinner = Spinner(
            text=str(now.day),
            values=[str(d) for d in range(1, 32)],
            size_hint=(1, 0.2)
        )

        # Hora
        self.hour_spinner = Spinner(
            text=str(now.hour),
            values=[f"{h:02d}" for h in range(0, 24)],
            size_hint=(1, 0.2)
        )

        # Minutos
        self.minute_spinner = Spinner(
            text=str(now.minute),
            values=[f"{m:02d}" for m in range(0, 60)],
            size_hint=(1, 0.2)
        )

        # Botón guardar
        save_btn = Button(text="Guardar", size_hint=(1, 0.3))
        save_btn.bind(on_release=self.save_datetime)

        # Añadir widgets
        self.add_widget(Label(text="Año"))
        self.add_widget(self.year_spinner)

        self.add_widget(Label(text="Mes"))
        self.add_widget(self.month_spinner)

        self.add_widget(Label(text="Día"))
        self.add_widget(self.day_spinner)

        self.add_widget(Label(text="Hora"))
        self.add_widget(self.hour_spinner)

        self.add_widget(Label(text="Minutos"))
        self.add_widget(self.minute_spinner)

        self.add_widget(save_btn)

    def update_days(self, instance, value):
        """Actualiza los días según el mes seleccionado."""
        year = int(self.year_spinner.text)
        month = int(value)
        last_day = calendar.monthrange(year, month)[1]

        self.day_spinner.values = [str(d) for d in range(1, last_day + 1)]
        if int(self.day_spinner.text) > last_day:
            self.day_spinner.text = "1"

    def save_datetime(self, instance):
        year = self.year_spinner.text
        month = self.month_spinner.text
        day = self.day_spinner.text
        hour = self.hour_spinner.text
        minute = self.minute_spinner.text

        fecha = f"{year}-{month}-{day}"
        hora = f"{hour}:{minute}:00"

        comando = f"sudo date -s '{fecha} {hora}'"
        os.system(comando)

        App.get_running_app().popup.dismiss()


class MainApp(App):

    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20)

        btn = Button(text="Cambiar Fecha y Hora", size_hint=(1, 0.2))
        btn.bind(on_release=self.open_popup)

        layout.add_widget(btn)
        return layout

    def open_popup(self, instance):
        content = DateTimePopup()
        self.popup = Popup(
            title="Configurar Fecha y Hora",
            content=content,
            size_hint=(0.8, 0.9)
        )
        self.popup.open()


if __name__ == "__main__":
    MainApp().run()
