from gpiozero import Device
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import LED, Button
from time import sleep

Device.pin_factory = PiGPIOFactory()

PIN_EMERGENCY = 2
PIN_SENSOR = 3
PIN_MARCHA = 4
PIN_BOCINA = 17


def check_pin_free(pin):
    try:
        test_led = LED(pin)
        test_led.close()
        return True
    except Exception as e:
        print(f"Error al acceder al pin {pin}: {e}")
        return False


if not all(
    [
        check_pin_free(PIN_BOCINA),
        check_pin_free(PIN_MARCHA),
        check_pin_free(PIN_SENSOR),
        check_pin_free(PIN_EMERGENCY),
    ]
):
    print("Uno o más pines están ocupados. No puedo iniciar la aplicación.")
else:
    output_bocina = LED(PIN_BOCINA)
    output_marcha = LED(PIN_MARCHA)
    input_sensor = Button(PIN_SENSOR, pull_up=True)
    input_emergency = Button(PIN_EMERGENCY, pull_up=True)

    try:
        print("Inicia pruebas de pines")

        while True:
            output_marcha.off()
            output_bocina.off()

            if input_sensor.is_pressed:
                output_marcha.on()

            if not input_emergency.is_pressed:
                output_bocina.on()

            sleep(0.1)

    except KeyboardInterrupt:
        print("Interrupción por teclado")
        output_marcha.off()
        output_bocina.off()

    finally:
        input_emergency.close()
        input_sensor.close()

        output_marcha.off()
        output_bocina.off()

        output_bocina.close()
        output_marcha.close()

        print("FIN")
