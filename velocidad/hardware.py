import logging
from gpiozero import Device
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import LED, Button

Device.pin_factory = PiGPIOFactory()
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)
log = logging.getLogger(__name__)

# pines de entrada # header numeracion fisica
PIN_INPUT_GPIO_4 = 4 # 7
PIN_INPUT_EMERGENCY = 17  # 11
PIN_INPUT_SENSOR = 27  # 13
PIN_INPUT_GPIO_22 = 22 # 15

# configuraciones
TIEMPO_REBOTE_SENSOR = 0.01 # 10 milisegundos

# watch -n 0.1 gpioget gpiochip0 27

def check_pin_free(pin):
    try:
        test_ = Button(pin)
        test_.close()
        log.info(f"Pin:{pin} revisado")
        return True
    except Exception as e:
        log.error(f"Error al acceder al pin {pin}: {e}")
        return False


if not all(
    [
        check_pin_free(PIN_INPUT_SENSOR),
        check_pin_free(PIN_INPUT_EMERGENCY),
        check_pin_free(PIN_INPUT_GPIO_4),
        check_pin_free(PIN_INPUT_GPIO_22)
    ]
):
    log.error("error in pins selected")
    raise SystemError
# configuracion de pines entrada
input_emergency = Button(PIN_INPUT_EMERGENCY, pull_up=True, bounce_time=TIEMPO_REBOTE_SENSOR)
input_sensor = Button(PIN_INPUT_SENSOR, pull_up=True, bounce_time=TIEMPO_REBOTE_SENSOR)
input_gpio_4= Button(PIN_INPUT_GPIO_4, pull_up=True, bounce_time=TIEMPO_REBOTE_SENSOR)
input_gpio_22 = Button(PIN_INPUT_GPIO_22, pull_up=True, bounce_time=TIEMPO_REBOTE_SENSOR)

def close_all_pins():
#pines cerrados
    input_emergency.close()
    input_sensor.close()
    input_gpio_4.close()
    input_gpio_22.close()
    log.info("close all pins")