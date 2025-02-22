from pins_config import *

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
    input_emergency.close()
    input_sensor.close()

    output_marcha.off()
    output_bocina.off()

    output_bocina.close()
    output_marcha.close()

    print("FIN")
