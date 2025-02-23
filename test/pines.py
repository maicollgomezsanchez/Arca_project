from hardware import (
    output_bocina,
    input_sensor,
    input_emergency,
    output_moneda,
    output_marcha,
    close_all_pins
)

try:
    print("Inicia pruebas de pines")
    input_sensor.when_pressed = output_marcha.on
    input_sensor.when_released = output_marcha.off
    input_emergency.when_pressed = output_bocina.on
    input_emergency.when_released = output_bocina.off

    while True:
        pass

except KeyboardInterrupt:
    print("Interrupción por teclado")
    output_marcha.off()
    output_bocina.off()

finally:
    close_all_pins()
    print("FIN")
