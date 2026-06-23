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
        super().__init__(orientation='vertical', spacing=5, padding=5, **kwargs)

        now = datetime.now()

        # Tamaños optimizados para 800x400
        spinner_font = 22
        label_font = 24
        button_font = 26
        spinner_height = 45

        from kivy.uix.gridlayout import GridLayout
        grid = GridLayout(cols=2, spacing=4, size_hint=(1, 0.70))

        # Año
        grid.add_widget(Label(text="Año", font_size=label_font))
        self.year_spinner = Spinner(
            text=str(now.year),
            values=[str(y) for y in range(2025, 2051)],
            size_hint=(1, None),
            height=spinner_height,
            font_size=spinner_font
        )
        grid.add_widget(self.year_spinner)

        # Mes
        grid.add_widget(Label(text="Mes", font_size=label_font))
        self.month_spinner = Spinner(
            text=str(now.month),
            values=[str(m) for m in range(1, 13)],
            size_hint=(1, None),
            height=spinner_height,
            font_size=spinner_font
        )
        self.month_spinner.bind(text=self.update_days)
        grid.add_widget(self.month_spinner)

        # Día
        grid.add_widget(Label(text="Día", font_size=label_font))
        self.day_spinner = Spinner(
            text=str(now.day),
            values=[str(d) for d in range(1, 32)],
            size_hint=(1, None),
            height=spinner_height,
            font_size=spinner_font
        )
        grid.add_widget(self.day_spinner)

        # Hora
        grid.add_widget(Label(text="Hora", font_size=label_font))
        self.hour_spinner = Spinner(
            text=f"{now.hour:02d}",
            values=[f"{h:02d}" for h in range(0, 24)],
            size_hint=(1, None),
            height=spinner_height,
            font_size=spinner_font
        )
        grid.add_widget(self.hour_spinner)

        # Minutos
        grid.add_widget(Label(text="Minutos", font_size=label_font))
        self.minute_spinner = Spinner(
            text=f"{now.minute:02d}",
            values=[f"{m:02d}" for m in range(0, 60)],
            size_hint=(1, None),
            height=spinner_height,
            font_size=spinner_font
        )
        grid.add_widget(self.minute_spinner)

        self.add_widget(grid)

        # Botones
        btn_layout = BoxLayout(size_hint=(1, 0.15), spacing=8)

        save_btn = Button(text="Guardar", font_size=button_font)
        save_btn.bind(on_release=self.save_datetime)

        exit_btn = Button(text="Salir", font_size=button_font)
        exit_btn.bind(on_release=self.close_popup)

        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(exit_btn)

        self.add_widget(btn_layout)

    def close_popup(self, instance):
        self.popup.dismiss()

    def update_days(self, instance, value):
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

        self.popup.dismiss()

