import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# Intentar cargar gpiozero
try:
    from gpiozero import Button, LED

    GPIO_AVAILABLE = True
    log.info("gpiozero cargado correctamente")

except ImportError:
    GPIO_AVAILABLE = False
    log.warning("gpiozero NO disponible, usando modo simulado")

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
PIN_OUTPUT_TRAGA_FICHA = 24  # 18
PIN_OUTPUT_LUCES = 25 # 22
PIN_OUTPUT_GPIO_12 = 12 # 32
# configuraciones
TIEMPO_DURACION_SIRENA = 2
TIEMPO_ONE_SEC = 1
TIEMPO_100_MSEC = 0.1 # 100 milisegundos
MAXIMAS_VUELTAS = 50
TIEMPO_MAXIMO_ESPERA = 600 # minutos
TIEMPO_REBOTE = 0.1  # 100 milisegundos
TIEMPO_RETARDO_LUCES = 0.5 # 500 milisegundos
MAXIMO_PULSOS_FICHA = 3 # pulsos 
TIEMPO_PULSOS_FICHA = 0.300 # 500 milisengundos

START, STOP, PAUSE, MANUAL, AUTO, SEMI = (
    "START",
    "STOP",
    "PAUSE",
    "MANUAL",
    "AUTO",
    "SEMI",
)

if GPIO_AVAILABLE:
    # configuracion de pines salida
    output_bocina = LED(PIN_OUTPUT_BOCINA, initial_value=False)
    output_marcha = LED(PIN_OUTPUT_MARCHA, initial_value=False)
    output_traga_ficha = LED(PIN_OUTPUT_TRAGA_FICHA, initial_value=False)
    # configuracion de pines entrada
    input_emergency = Button(PIN_INPUT_EMERGENCY, pull_up=False, bounce_time=TIEMPO_REBOTE)
    def close_all_pins():
    # outputs apagadas
        output_bocina.off()
        output_marcha.off()
        output_traga_ficha.off()
    #pines cerrados
        output_bocina.close()
        output_marcha.close()
        output_traga_ficha.close()
        input_emergency.close()
        log.info("close all pins")
    
else:
    # Modo simulado
    class Pin:
        def __init__(self):
            self.is_lit = None
        
        def on(self):
            self.is_lit = True
            return self.is_lit

        def off(self):
            self.is_lit = False
            return self.is_lit
        
        def wait_for_press(self):
            return True

        def wait_for_release(self):
            return True
        
        def is_pressed(self):
            return True
        # configuracion de pines salida
    output_bocina = Pin()
    output_marcha = Pin()
    output_traga_ficha = Pin()
    # configuracion de pines entrada
    input_emergency = Pin()
    
    def close_all_pins():
        log.info("Modo simulado: no hay pines que cerrar")