import logging
from gpiozero import Device
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import LED, Button

Device.pin_factory = PiGPIOFactory()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# botones a 3V3
# pines de entrada # header numeracion fisica
# GND 9
PIN_EMERGENCY = 17  # 11
PIN_SENSOR = 27  # 13
# pines remotos
# GND 14 , 20
PIN_REMOTO_MARCHA = 18  # 12
PIN_REMOTO_PARO = 23  # 16
PIN_REMOTO_PAUSA = 24  # 18
PIN_REMOTO_BOCINA = 25  # 22
# pines de salida
# GND 39
PIN_MARCHA = 5  # 29
PIN_BOCINA = 6  # 31
PIN_MONEDA = 13  # 33
# configuraciones
TIEMPO_SIRENA = 2
TIEMPO_1_SEC = 1
MAX_LAPS = 50
BOUNCE_TIME = 0.15

START, STOP, PAUSE, MANUAL, AUTO, SEMI = (
    "START",
    "STOP",
    "PAUSE",
    "MANUAL",
    "AUTO",
    "SEMI",
)


class Hardware:
    initialized_pins = []

    def __init__(self, _pin, _type):
        self._pin = None
        try:
            if _type == Button:
                self._pin = Button(
                    pin=_pin,
                    pull_up=True,
                    bounce_time=BOUNCE_TIME,
                )

            elif _type == LED:
                self._pin = LED(_pin, initial_value=False)
            if self._pin:
                self.initialized_pins.append(self._pin)
        
        except Exception as e:
            log.error(f"Error al acceder al pin {_pin}: {e}")
            if self._pin:
                self._pin.close()

    def close(self):
        if isinstance(self._pin, LED):
            self._pin.off()
        if self._pin:
            self._pin.close()

    def on(self):
        if isinstance(self._pin, LED):
            self._pin.on()

    def off(self):
        if isinstance(self._pin, LED):
            self._pin.off()

    def when_pressed(self):
        if isinstance(self._pin, Button):
            self._pin.when_pressed()

    def when_released(self):
        if isinstance(self._pin, Button):
            self._pin.when_released()

    @classmethod
    def close_all_pins(cls):
        for pin in cls.initialized_pins:
            pin.close()