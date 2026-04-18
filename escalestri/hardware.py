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
# pines remotos
PIN_INPUT_REMOTO_MARCHA = 5  # 29
PIN_INPUT_REMOTO_PARO = 6  # 31
PIN_INPUT_REMOTO_PAUSA = 13  # 33
PIN_INPUT_REMOTO_BOCINA = 26  # 37
# pines de salida
PIN_OUTPUT_MARCHA = 18  # 12
PIN_OUTPUT_BOCINA = 23  # 16
PIN_OUTPUT_TRAGA_MONEDA = 24  # 18
PIN_OUTPUT_LUCES = 25 # 22
PIN_OUTPUT_GPIO_12 = 12 # 32
# configuraciones
TIEMPO_DURACION_SIRENA = 2
TIEMPO_ONE_SEC = 1
TIEMPO_REBOTE_SENSOR = 0.1 # 100 milisegundos
MAXIMAS_VUELTAS = 50
TIEMPO_REBOTE = 0.1  # 100 milisegundos
TIEMPO_RETARDO_LUCES = 0.5 # 500 milisegundos

START, STOP, PAUSE, MANUAL, AUTO, SEMI = (
    "START",
    "STOP",
    "PAUSE",
    "MANUAL",
    "AUTO",
    "SEMI",
)


def check_pin_free(pin):
    try:
        test_led = Button(pin)
        test_led.close()
        log.info(f"Pin:{pin} revisado")
        return True
    except Exception as e:
        log.error(f"Error al acceder al pin {pin}: {e}")
        return False


if not all(
    [
        check_pin_free(PIN_OUTPUT_BOCINA),
        check_pin_free(PIN_OUTPUT_MARCHA),
        check_pin_free(PIN_INPUT_SENSOR),
        check_pin_free(PIN_INPUT_EMERGENCY),
        check_pin_free(PIN_INPUT_REMOTO_MARCHA),
        check_pin_free(PIN_INPUT_REMOTO_PARO),
        check_pin_free(PIN_INPUT_REMOTO_PAUSA),
        check_pin_free(PIN_INPUT_REMOTO_BOCINA),
        check_pin_free(PIN_OUTPUT_TRAGA_MONEDA),
        #nuevos pines
        check_pin_free(PIN_OUTPUT_LUCES),
        check_pin_free(PIN_OUTPUT_GPIO_12),
        check_pin_free(PIN_INPUT_GPIO_4),
        check_pin_free(PIN_INPUT_GPIO_22)
    ]
):
    log.error("error in pins selected")
    raise SystemError
# configuracion de pines salida
output_bocina = LED(PIN_OUTPUT_BOCINA, initial_value=False)
output_marcha = LED(PIN_OUTPUT_MARCHA, initial_value=False)
output_traga_monedas = LED(PIN_OUTPUT_TRAGA_MONEDA, initial_value=False)
output_luces = LED(PIN_OUTPUT_LUCES, initial_value=False)
output_gpio_12 = LED(PIN_OUTPUT_GPIO_12, initial_value=False)
# configuracion de pines entrada
input_emergency = Button(PIN_INPUT_EMERGENCY, pull_up=True, bounce_time=TIEMPO_REBOTE)
input_sensor = Button(PIN_INPUT_SENSOR, pull_up=True, bounce_time=TIEMPO_REBOTE_SENSOR)
input_gpio_4= Button(PIN_INPUT_GPIO_4, pull_up=True, bounce_time=TIEMPO_REBOTE)
input_gpio_22 = Button(PIN_INPUT_GPIO_22, pull_up=True, bounce_time=TIEMPO_REBOTE)

# configuracion de pines remotos
input_remote_marcha = Button(PIN_INPUT_REMOTO_MARCHA, pull_up=True, bounce_time=TIEMPO_REBOTE)
input_remote_paro = Button(PIN_INPUT_REMOTO_PARO, pull_up=True, bounce_time=TIEMPO_REBOTE)
input_remote_pausa = Button(PIN_INPUT_REMOTO_PAUSA, pull_up=True, bounce_time=TIEMPO_REBOTE)
input_remote_bocina = Button(PIN_INPUT_REMOTO_BOCINA, pull_up=True, bounce_time=TIEMPO_REBOTE)

def close_all_pins():
    # outputs apagadas
    output_bocina.off()
    output_marcha.off()
    output_traga_monedas.off()
    output_luces.off()
    output_gpio_12.off()
#pines cerrados
    output_bocina.close()
    output_marcha.close()
    output_traga_monedas.close()
    output_luces.close()
    output_gpio_12.close()
    input_emergency.close()
    input_sensor.close()
    input_gpio_4.close()
    input_gpio_22.close()
    input_remote_marcha.close()
    input_remote_paro.close()
    input_remote_pausa.close()
    input_remote_bocina.close()
    log.info("close all pins")