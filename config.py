# ===== CONFIGURACION (edita solo este archivo) =====
WIFI_SSID = "SECRETO"     # La Pico NO usa 5 GHz
WIFI_PASS = "SECRETO"
AIO_USER  = "SECRETO"
AIO_KEY   = "SECRETO"   # regenerala en Adafruit IO (la anterior quedo expuesta)

# Pines
PIN_TRIG_TANQUE, PIN_ECHO_TANQUE = 2, 3     # HC-SR04
PIN_TRIG_CIST,   PIN_ECHO_CIST   = 4, 5     # (2do ultrasonico, opcional)
PIN_FLUJO = 6          # YF-S201 (via divisor 5V -> 3.3V)
PIN_RELE  = 15
PIN_SDA, PIN_SCL = 8, 9      # I2C0 -> OLED
OLED_ADDR = 0x3C
USAR_OLED = True
RELE_ACTIVO_BAJO = False   # True si tu modulo rele enciende con 0 V

# Calibracion del nivel (distancia sensor->agua, cm). MIDELA con regla.
TANQUE_LLENO_CM = 4.0
TANQUE_VACIO_CM = 15.0
CIST_MIN_CM     = 22.0
USAR_CISTERNA   = False

# Logica de la bomba
NIVEL_BAJO = 30
NIVEL_ALTO = 90
T_ARRANQUE_MS = 5000
CAUDAL_MIN = 0.3
PULSOS_POR_LITRO = 450   # CALIBRALO: vierte 1 L real y cuenta pulsos (pruebas.py opcion 4)

PERIODO_NUBE_S = 20
