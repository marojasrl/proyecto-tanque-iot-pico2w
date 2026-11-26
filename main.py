# Tanque elevado IoT - Pico W / Pico 2 W - MicroPython + asyncio
# Tareas: sensores, flujo (PIO), control de bomba, nube (Adafruit IO), pantalla OLED (I2C)
import asyncio, time, network
from machine import Pin, I2C, time_pulse_us
import config as C
from pio_flow import FlowPIO
try:
    import requests
except ImportError:
    import urequests as requests

# ---------- hardware ----------
rele = Pin(C.PIN_RELE, Pin.OUT)
def bomba(on):
    rele.value((not on) if C.RELE_ACTIVO_BAJO else on)
    S["bomba"] = on
trig_t, echo_t = Pin(C.PIN_TRIG_TANQUE, Pin.OUT), Pin(C.PIN_ECHO_TANQUE, Pin.IN)
trig_c, echo_c = Pin(C.PIN_TRIG_CIST, Pin.OUT), Pin(C.PIN_ECHO_CIST, Pin.IN)
flujo = FlowPIO(C.PIN_FLUJO)

oled = None                                   # pantalla I2C (si falla, el sistema sigue)
if C.USAR_OLED:
    try:
        from oled import SSD1306
        i2c = I2C(0, sda=Pin(C.PIN_SDA), scl=Pin(C.PIN_SCL), freq=400_000)
        oled = SSD1306(i2c, C.OLED_ADDR)
    except Exception as e:
        print("OLED no disponible:", e)

# ---------- estado compartido ----------
S = {"bomba": False, "nivel": None, "cist": None, "caudal": 0.0,
     "litros": 0.0, "modo": "AUTO", "bloqueo": False, "alertas": [], "wifi": False}
bomba(False)

def alerta(msg):
    print("ALERTA:", msg)
    S["alertas"].append(msg)

def distancia(trig, echo):
    trig.off(); time.sleep_us(2)
    trig.on(); time.sleep_us(10); trig.off()
    t = time_pulse_us(echo, 1, 30000)
    return None if t < 0 else t * 0.0343 / 2

async def mediana(trig, echo):    # filtro: mediana de 5 lecturas (cede la CPU entre lecturas)
    v = []
    for _ in range(5):
        d = distancia(trig, echo)
        if d is not None: v.append(d)
        await asyncio.sleep_ms(30)
    v.sort()
    return round(v[len(v)//2], 1) if v else None

def a_porcentaje(d):
    p = (C.TANQUE_VACIO_CM - d) / (C.TANQUE_VACIO_CM - C.TANQUE_LLENO_CM) * 100
    return max(0, min(100, round(p)))

# ---------- tareas ----------
async def t_sensores():
    while True:
        d = await mediana(trig_t, echo_t)
        S["nivel"] = None if d is None else a_porcentaje(d)
        if C.USAR_CISTERNA:
            S["cist"] = await mediana(trig_c, echo_c)
        await asyncio.sleep_ms(500)

async def t_flujo():
    previo = flujo.total(); t0 = time.ticks_ms(); dia0 = t0
    while True:
        await asyncio.sleep(1)
        ahora = time.ticks_ms(); total = flujo.total()
        dp = (total - previo) & 0xFFFFFFFF
        dt = time.ticks_diff(ahora, t0) / 1000
        S["caudal"] = round(dp / dt / 7.5, 2)           # L/min
        S["litros"] += dp / C.PULSOS_POR_LITRO
        previo, t0 = total, ahora
        if time.ticks_diff(ahora, dia0) > 86_400_000:
            S["litros"] = 0.0; dia0 = ahora

async def t_control():
    t_on = 0
    while True:
        n, modo = S["nivel"], S["modo"]
        cist_ok = (not C.USAR_CISTERNA) or (S["cist"] is not None and S["cist"] <= C.CIST_MIN_CM)
        if S["bomba"]:
            if modo == "OFF" or S["bloqueo"]:
                bomba(False)
            elif n is None:
                bomba(False); alerta("SENSOR_NIVEL_FALLA")
            elif n >= C.NIVEL_ALTO:
                bomba(False); alerta("TANQUE_LLENO_BOMBA_APAGADA")
            elif C.USAR_CISTERNA and not cist_ok:
                bomba(False); alerta("CISTERNA_VACIA")
            elif time.ticks_diff(time.ticks_ms(), t_on) > C.T_ARRANQUE_MS \
                    and S["caudal"] < C.CAUDAL_MIN:
                bomba(False); S["bloqueo"] = True
                alerta("BOMBA_EN_SECO")
        else:
            if modo == "AUTO" and not S["bloqueo"] and n is not None \
                    and n <= C.NIVEL_BAJO and cist_ok:
                bomba(True); t_on = time.ticks_ms()
        await asyncio.sleep_ms(300)

AIO = "https://io.adafruit.com/api/v2/" + C.AIO_USER
HDR = {"X-AIO-Key": C.AIO_KEY, "Content-Type": "application/json"}

def aio_post(feed, valor):
    r = requests.post(AIO + "/feeds/%s/data" % feed, json={"value": valor}, headers=HDR)
    r.close()

def aio_ultimo(feed):
    r = requests.get(AIO + "/feeds/%s/data/last" % feed, headers=HDR)
    try: return r.json()["value"]
    finally: r.close()

async def t_nube():
    wlan = network.WLAN(network.STA_IF); wlan.active(True)
    while True:
        S["wifi"] = wlan.isconnected()
        if not S["wifi"]:                               # reconexion automatica
            print("Conectando Wi-Fi...")
            try: wlan.connect(C.WIFI_SSID, C.WIFI_PASS)
            except Exception as e: print(e)
            for _ in range(20):
                if wlan.isconnected(): break
                await asyncio.sleep(1)
            continue
        try:
            while S["alertas"]:
                aio_post("alerta", S["alertas"].pop(0))
            if S["nivel"] is not None: aio_post("nivel", S["nivel"])
            aio_post("caudal", S["caudal"])
            aio_post("litros", round(S["litros"], 2))
            aio_post("bomba", 1 if S["bomba"] else 0)
            cmd = aio_ultimo("modo")                    # accion remota
            if cmd == "RESET":
                S["bloqueo"] = False; S["modo"] = "AUTO"
                aio_post("modo", "AUTO")                # evita que RESET se repita cada ciclo
            elif cmd in ("AUTO", "OFF"):
                S["modo"] = cmd
        except Exception as e:
            print("Error nube:", e)
        await asyncio.sleep(C.PERIODO_NUBE_S)

async def t_oled():
    if oled is None:
        return
    while True:
        try:
            o, n = oled, S["nivel"]
            o.fill(0)
            o.text("TANQUE ELEVADO", 8, 0)
            o.text("Nivel: " + ("--" if n is None else "%d%%" % n), 0, 12)
            o.rect(0, 22, 128, 8, 1)
            if n: o.fill_rect(2, 24, int(124 * n / 100), 4, 1)
            o.text("Caudal:%.1fL/m" % S["caudal"], 0, 34)
            o.text("Litros: %.2f" % S["litros"], 0, 44)
            if S["bloqueo"]:
                o.fill_rect(0, 54, 128, 10, 1); o.text("BLOQ: BOMBA SECO", 0, 55, 0)
            else:
                o.text("B:%s %s %s" % ("ON " if S["bomba"] else "OFF", S["modo"],
                                       "WiFi" if S["wifi"] else "noWF"), 0, 54)
            o.show()
        except Exception as e:
            print("OLED:", e)
        await asyncio.sleep_ms(1000)

async def t_consola():
    while True:
        print("Nivel:", S["nivel"], "% | Caudal:", S["caudal"], "L/min | Litros:",
              round(S["litros"], 2), "| Bomba:", S["bomba"], "| Modo:", S["modo"],
              "| Bloqueo:", S["bloqueo"], "| WiFi:", S["wifi"])
        await asyncio.sleep(2)

async def main():
    await asyncio.gather(t_sensores(), t_flujo(), t_control(), t_nube(), t_oled(), t_consola())

try:
    asyncio.run(main())
finally:
    bomba(False)     # al detener con Stop, la bomba queda apagada
