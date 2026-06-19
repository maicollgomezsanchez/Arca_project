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


# pines de entrada # header numeracion fisica
PIN_INPUT_GPIO_4 = 4 # 7
PIN_INPUT_EMERGENCY = 27  # 13
PIN_INPUT_SENSOR = 17  # 11
PIN_INPUT_GPIO_22 = 22 # 15

TIEMPO_REBOTE_SENSOR = 0.300 # 300 milisegundos
PULL_UP = True
PULL_DOWN = False
Pull = PULL_DOWN

def check_pin_free(pin):
    if not GPIO_AVAILABLE:
        return True  # En modo simulado, siempre OK

    try:
        test_ = Button(pin)
        test_.close()
        log.info(f"Pin {pin} revisado")
        return True
    except Exception as e:
        log.error(f"Error al acceder al pin {pin}: {e}")
        return False


if GPIO_AVAILABLE:
    if not all([
        check_pin_free(PIN_INPUT_SENSOR),
        check_pin_free(PIN_INPUT_EMERGENCY),
        check_pin_free(PIN_INPUT_GPIO_4),
        check_pin_free(PIN_INPUT_GPIO_22)
    ]):
        log.error("Error en los pines seleccionados")
        raise SystemError

    # Configurar pines reales
    input_emergency = Button(PIN_INPUT_EMERGENCY, pull_up=Pull, bounce_time=TIEMPO_REBOTE_SENSOR)
    input_sensor = Button(PIN_INPUT_SENSOR, pull_up=Pull, bounce_time=TIEMPO_REBOTE_SENSOR)
    input_gpio_4 = Button(PIN_INPUT_GPIO_4, pull_up=Pull, bounce_time=TIEMPO_REBOTE_SENSOR)
    input_gpio_22 = Button(PIN_INPUT_GPIO_22, pull_up=Pull, bounce_time=TIEMPO_REBOTE_SENSOR)

    def close_all_pins():
        input_emergency.close()
        input_sensor.close()
        input_gpio_4.close()
        input_gpio_22.close()
        log.info("Pines cerrados correctamente")

else:
    # Modo simulado
    input_emergency = True
    input_sensor = True
    input_gpio_4 = True
    input_gpio_22 = True

    def close_all_pins():
        log.info("Modo simulado: no hay pines que cerrar")