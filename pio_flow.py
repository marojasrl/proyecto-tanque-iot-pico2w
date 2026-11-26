# RETO DE ARQUITECTURA: conteo de pulsos del YF-S201 con una maquina PIO.
# La PIO cuenta flancos de subida por hardware: la CPU no atiende ninguna
# interrupcion; solo "lee" el contador cuando lo necesita.
import rp2
from machine import Pin

@rp2.asm_pio()
def _contador():
    wait(0, pin, 0)        # espera nivel bajo
    wait(1, pin, 0)        # espera flanco de subida
    jmp(x_dec, "n")        # x = x - 1  (salta igual a la siguiente linea)
    label("n")

class FlowPIO:
    def __init__(self, pin_num, sm_id=0):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.sm = rp2.StateMachine(sm_id, _contador, freq=2_000_000,
                                   in_base=self.pin)
        self.sm.exec("set(x, 0)")
        self.sm.active(1)

    def total(self):
        """Pulsos acumulados desde el arranque (lee x sin detener la PIO)."""
        self.sm.exec("in_(x, 32)")
        self.sm.exec("push()")
        return (-self.sm.get()) & 0xFFFFFFFF
