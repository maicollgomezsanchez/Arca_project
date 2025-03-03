from Hardware import Hardware, PIN_BOCINA, PIN_SENSOR, PIN_EMERGENCY, PIN_MARCHA, LED, Button

# Creando instancias de pines
output_bocina = Hardware(PIN_BOCINA, LED)
output_marcha = Hardware(PIN_MARCHA, LED)
input_emergency = Hardware(PIN_EMERGENCY, Button)
input_sensor = Hardware(PIN_SENSOR, Button)

try:
    print("Inicia pruebas de pines")
    input_sensor.when_pressed = output_marcha._pin.on  # Accediendo al pin específico
    input_sensor._pin.when_released = output_marcha._pin.off  # Accediendo al pin específico
    input_emergency._pin.when_pressed = output_bocina._pin.on  # Accediendo al pin específico
    input_emergency._pin.when_released = output_bocina._pin.off  # Accediendo al pin específico

    while True:
        pass

except KeyboardInterrupt:
    print("InterrupciOn por teclado")
    output_marcha._pin.off()
    output_bocina._pin.off()

finally:
    Hardware.close_all_pins()  
    
    print("FIN")
