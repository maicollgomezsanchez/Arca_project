import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# Intentar cargar gpiozero
try:
    from gpiozero import Button
    GPIO_AVAILABLE = True
    log.info("gpiozero cargado correctamente")
except ImportError:
    GPIO_AVAILABLE = False
    log.warning("gpiozero NO disponible, usando modo simulado")


# Pines físicos
PIN_INPUT_GPIO_4 = 4      # pin 7
PIN_INPUT_GPIO_27 = 27  # pin 13
PIN_INPUT_GPIO_17 = 17     # pin 11
PIN_INPUT_GPIO_22 = 22    # pin 15

TIEMPO_REBOTE_SENSOR = 0.005 # 5 milisegundos
PULL_UP = True
PULL_DOWN = False
Pull = PULL_DOWN

# Lista de pines válidos para el sensor
SENSOR_PINS = [PIN_INPUT_GPIO_17,PIN_INPUT_GPIO_27, PIN_INPUT_GPIO_4, PIN_INPUT_GPIO_22]

class SensorVirtual:
    def __init__(self, pins, pull_up=True, bounce=0.05):
        self.buttons = []
        self._when_pressed = None
        self._when_released = None
        self.last_pin = None  # opcional (para debug / SCADA)

        for pin in pins:
            try:
                btn = Button(pin, pull_up=pull_up, bounce_time=bounce)
                self.buttons.append(btn)
                btn.when_pressed = lambda p=pin: self._pressed(p)
                btn.when_released = lambda p=pin: self._released(p)
                log.info(f"SensorVirtual: Pin {pin} inicializado")
            except Exception as e:
                log.error(f"SensorVirtual: Error en pin {pin}: {e}")

    def _pressed(self, pin):
        self.last_pin = pin
        log.info(f"SensorVirtual: ACTIVADO por pin {pin}")
        if self._when_pressed:
            self._when_pressed()

    def _released(self, pin):
        log.info(f"SensorVirtual: DESACTIVADO por pin {pin}")
        if self._when_released:
            self._when_released()

    @property
    def when_pressed(self):
        return self._when_pressed

    @when_pressed.setter
    def when_pressed(self, fn):
        self._when_pressed = fn

    @property
    def when_released(self):
        return self._when_released

    @when_released.setter
    def when_released(self, fn):
        self._when_released = fn

    def close(self):
        for btn in self.buttons:
            btn.close()
        log.info("SensorVirtual: pines cerrados")


# ---------------------------------------------------------
#  INICIALIZACIÓN DE HARDWARE
# ---------------------------------------------------------
def check_pin_free(pin):
    if not GPIO_AVAILABLE:
        return True

    try:
        test_ = Button(pin)
        test_.close()
        log.info(f"Pin {pin} revisado")
        return True
    except Exception as e:
        log.error(f"Error al acceder al pin {pin}: {e}")
        return False


if GPIO_AVAILABLE:

    # Revisar todos los pines
    for pin in SENSOR_PINS:
        check_pin_free(pin)

    # Sensor virtual que escucha varios pines
    input_sensor = SensorVirtual(
        pins=SENSOR_PINS,
        pull_up=Pull,
        bounce=TIEMPO_REBOTE_SENSOR
    )

    def close_all_pins():
        input_sensor.close()
        log.info("Pines cerrados correctamente")

else:
    # Modo simulado
    input_emergency = True
    input_sensor = True
    input_gpio_4 = True
    input_gpio_22 = True

    def close_all_pins():
        log.info("Modo simulado: no hay pines que cerrar")