import logging
from gpiozero import Device
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import LED, Button

Device.pin_factory = PiGPIOFactory()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# pines de entrada # header numeracion fisica
PIN_EMERGENCY = 17  # 11
PIN_SENSOR = 27  # 13
# pines remotos
PIN_REMOTO_MARCHA = 18  # 12
PIN_REMOTO_PARO = 23  # 16
PIN_REMOTO_PAUSA = 24  # 18
PIN_REMOTO_BOCINA = 25  # 22
# pines de salida
PIN_MARCHA = 5  # 29
PIN_BOCINA = 6  # 31
PIN_MONEDA = 13  # 33
# configuraciones
TIEMPO_SIRENA = 2
TIEMPO_1_SEC = 1
MAX_LAPS = 50
BOUNCE_TIME = 0.3
OUTPUT = 1
INPUT = 0

START, STOP, PAUSE, MANUAL, AUTO, SEMI = (
    "START",
    "STOP",
    "PAUSE",
    "MANUAL",
    "AUTO",
    "SEMI",
)


def check_pin_free(pin, type):
    try:
        if type == INPUT:
            test_led = Button(pin)
        else:
            test_led = LED(pin)
        test_led.close()
        return True
    except Exception as e:
        log.error(f"Error al acceder al pin {pin}: {e}")
        return False


if not all(
    [
        check_pin_free(PIN_BOCINA, OUTPUT),
        check_pin_free(PIN_MARCHA, OUTPUT),
        check_pin_free(PIN_MONEDA, OUTPUT),
        check_pin_free(PIN_EMERGENCY , INPUT),
        check_pin_free(PIN_SENSOR, INPUT),
        check_pin_free(PIN_REMOTO_MARCHA, INPUT),
        check_pin_free(PIN_REMOTO_PARO, INPUT),
        check_pin_free(PIN_REMOTO_PAUSA, INPUT),
        check_pin_free(PIN_REMOTO_BOCINA, INPUT),
    ]
):
    log.error("error in pins selected")
    raise SystemError
# configuracion de pines
output_bocina = LED(PIN_BOCINA, initial_value=False)
output_marcha = LED(PIN_MARCHA, initial_value=False)
output_moneda = LED(PIN_MONEDA, initial_value=False)
input_emergency = Button(PIN_EMERGENCY, bounce_time=BOUNCE_TIME)
input_sensor = Button(PIN_SENSOR,  bounce_time=BOUNCE_TIME)
input_remote_marcha = Button(PIN_REMOTO_MARCHA, bounce_time=BOUNCE_TIME)
input_remote_paro = Button(PIN_REMOTO_PARO,  bounce_time=BOUNCE_TIME)
input_remote_pausa = Button(PIN_REMOTO_PAUSA,  bounce_time=BOUNCE_TIME)
input_remote_bocina = Button(PIN_REMOTO_BOCINA, bounce_time=BOUNCE_TIME)

def close_all_pins():
    output_bocina.close()
    output_marcha.close()
    output_moneda.close()
    input_emergency.close()
    input_sensor.close()
    input_remote_marcha.close()
    input_remote_paro.close()
    input_remote_pausa.close()
    input_remote_bocina.close()