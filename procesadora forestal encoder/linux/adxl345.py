
import os
import re
import threading
import subprocess

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class ADXL345App(App):

    def build(self):
        self.process = None
        self.reader_thread = None

        root = BoxLayout(
            orientation="vertical",
            padding=25,
            spacing=15
        )

        root.add_widget(Label(
            text="Monitor ADXL345",
            font_size="28sp",
            size_hint_y=0.2
        ))

        self.x_label = Label(text="X: -- g", font_size="24sp")
        self.y_label = Label(text="Y: -- g", font_size="24sp")
        self.z_label = Label(text="Z: -- g", font_size="24sp")

        root.add_widget(self.x_label)
        root.add_widget(self.y_label)
        root.add_widget(self.z_label)

        self.status = Label(
            text="Sensor detenido",
            font_size="16sp",
            size_hint_y=0.2
        )
        root.add_widget(self.status)

        self.button = Button(
            text="Iniciar lectura",
            font_size="20sp",
            size_hint_y=0.25
        )
        self.button.bind(on_press=self.toggle_sensor)
        root.add_widget(self.button)

        return root

    def toggle_sensor(self, instance):
        if self.process is None:
            self.start_sensor()
        else:
            self.stop_sensor()

    def start_sensor(self):
        executable = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "adxl345"
        )

        try:
            self.process = subprocess.Popen(
                ["stdbuf", "-oL", executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except Exception as error:
            self.process = None
            self.status.text = f"Error: {error}"
            return

        self.status.text = "Conectando con el sensor..."
        self.button.text = "Detener lectura"

        self.reader_thread = threading.Thread(
            target=self.read_sensor,
            daemon=True
        )
        self.reader_thread.start()

    def read_sensor(self):
        pattern = re.compile(
            r"X:\s*([-+]?\d+(?:\.\d+)?)\s*g\s*\|\s*"
            r"Y:\s*([-+]?\d+(?:\.\d+)?)\s*g\s*\|\s*"
            r"Z:\s*([-+]?\d+(?:\.\d+)?)\s*g"
        )

        process = self.process

        try:
            for line in process.stdout:
                match = pattern.search(line)

                if match:
                    x, y, z = match.groups()
                    Clock.schedule_once(
                        lambda dt, a=x, b=y, c=z:
                        self.update_values(a, b, c),
                        0
                    )

            return_code = process.wait()

            if self.process is process:
                Clock.schedule_once(
                    lambda dt: self.sensor_finished(return_code),
                    0
                )

        except (OSError, ValueError) as error:
            Clock.schedule_once(
                lambda dt, msg=str(error): self.show_error(msg),
                0
            )

    def update_values(self, x, y, z):
        self.x_label.text = f"X: {float(x):+.3f} g"
        self.y_label.text = f"Y: {float(y):+.3f} g"
        self.z_label.text = f"Z: {float(z):+.3f} g"
        self.status.text = "Sensor conectado"

    def stop_sensor(self):
        process = self.process
        self.process = None

        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        self.button.text = "Iniciar lectura"
        self.status.text = "Sensor detenido"

    def sensor_finished(self, return_code):
        if self.process is not None:
            self.process = None
            self.button.text = "Iniciar lectura"
            self.status.text = (
                f"El programa terminó (código {return_code})"
            )

    def show_error(self, message):
        self.status.text = f"Error de lectura: {message}"

    def on_stop(self):
        self.stop_sensor()


if __name__ == "__main__":
    ADXL345App().run()
