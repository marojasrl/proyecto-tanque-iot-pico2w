# proyecto-tanque-iot-pico2w

Diseño e implementación de un sistema IoT con Raspberry Pi Pico 2 W para la gestión de un tanque elevado y su electrobomba. Proyecto final del curso **Arquitectura del Computador I 2026-2**.

## Descripción del proyecto

Sistema embebido IoT sobre la Raspberry Pi Pico 2 W que automatiza el llenado de un tanque elevado, protege la electrobomba y monitorea el consumo de agua en tiempo real, tanto de forma local (pantalla OLED) como remota (dashboard en Adafruit IO).

###Video Demo: https://youtube.com/shorts/uTs8DoL77X4

### Problema que resuelve

- **Desbordes de agua:** apaga automáticamente la bomba cuando el nivel alcanza el límite superior.
- **Protección contra marcha en seco:** verifica el flujo real en la tubería con un caudalímetro. Si la bomba funciona sin paso de agua, se apaga, queda bloqueada y emite una alerta.
- **Telemetría y consumo:** registra los litros acumulados del día y envía alertas a la nube ante fallas del sensor, tanque lleno o bomba en seco.

## Arquitectura y componentes

### Hardware

| Componente | Función |
|---|---|
| Raspberry Pi Pico 2 W (RP2350) | Microcontrolador principal con Wi-Fi |
| HC-SR04 (x2) | Sensores ultrasónicos de distancia. El **primero** mide el nivel del tanque; el **segundo** está previsto para la cisterna, pero está deshabilitado en la versión actual (`USAR_CISTERNA = False`) |
| YF-S201 | Caudalímetro de efecto Hall (salida conectada mediante divisor de tensión 5 V → 3.3 V) |
| Módulo L298N | Driver de potencia que conmuta la electrobomba (`IN1` y `ENA` unidos a GP5) |
| Electrobomba DC | Actuador de llenado |
| Pantalla OLED I2C SSD1306 128x64 | Visualización local de nivel, caudal, litros y estado |

### Conexiones (GPIO)

| Señal | Pin |
|---|---|
| HC-SR04 tanque: TRIG / ECHO | GP2 / GP3 |
| YF-S201 (señal de caudal) | GP6 |
| L298N (IN1 + ENA, bomba) | GP5 |
| OLED SDA / SCL (I2C por software) | GP9 / GP8 |

> El pin ECHO del HC-SR04 y la señal del YF-S201 entregan 5 V: deben pasar por un divisor de tensión antes de entrar a la Pico (3.3 V).

### Software

- **Lenguaje:** MicroPython con concurrencia cooperativa (`asyncio`).
- **Tareas concurrentes:**
  - `t_sensores`: lectura del nivel con filtro de mediana de 5 muestras.
  - `t_flujo`: cálculo de caudal (L/min) y litros acumulados, con reinicio cada 24 h.
  - `t_control`: lógica de la bomba y protecciones.
  - `t_nube`: reconexión Wi-Fi, publicación de datos y lectura de comandos remotos.
  - `t_oled`: actualización de la pantalla.
  - `t_consola`: salida de depuración por puerto serie.

### Reto de arquitectura (PIO)

El conteo de pulsos del YF-S201 se realiza con una máquina de estados **PIO** (`pio_flow.py`) que detecta los flancos de subida por hardware. La CPU ARM Cortex-M33 no atiende ninguna interrupción por pulso: solo lee el contador acumulado cuando lo necesita, quedando libre para el resto de tareas.

### Conectividad y nube

La telemetría se publica mediante **HTTP (API REST)** en **Adafruit IO**, con un ciclo de envío cada 20 s.

| Feed | Dirección | Contenido |
|---|---|---|
| `nivel` | Pico → nube | Nivel del tanque (%) |
| `caudal` | Pico → nube | Caudal (L/min) |
| `litros` | Pico → nube | Litros acumulados del día |
| `bomba` | Pico → nube | Estado de la bomba (1 = ON, 0 = OFF) |
| `alerta` | Pico → nube | Mensajes de alerta |
| `modo` | Nube → Pico | Comandos remotos: `AUTO`, `OFF`, `RESET` |

### Fabricación 3D

Tapa funcional para el tanque con soporte integrado para el sensor ultrasónico HC-SR04, que lo mantiene fijo y orientado hacia la superficie del agua.

> El HC-SR04 no es resistente al agua: debe montarse en la tapa sin contacto directo con el líquido ni con la condensación.

## Lógica de control

| Parámetro | Valor | Descripción |
|---|---|---|
| `NIVEL_BAJO` | 30 % | La bomba se enciende (modo AUTO) |
| `NIVEL_ALTO` | 90 % | La bomba se apaga |
| `T_ARRANQUE_MS` | 5000 ms | Tiempo de gracia antes de verificar flujo |
| `CAUDAL_MIN` | 0.3 L/min | Flujo mínimo para considerar que la bomba mueve agua |

**Protecciones y alertas:**

- `SENSOR_NIVEL_FALLA`: sin lectura válida del sensor, la bomba se apaga.
- `TANQUE_LLENO_BOMBA_APAGADA`: se alcanzó el nivel alto.
- `BOMBA_EN_SECO`: sin flujo tras el tiempo de arranque. La bomba se apaga y queda **bloqueada** hasta recibir `RESET`.
- `CISTERNA_VACIA`: solo si se habilita el segundo sensor.

**Modos de operación (feed `modo`):**

- `AUTO`: control automático por nivel.
- `OFF`: bomba apagada de forma forzada.
- `RESET`: libera el bloqueo y vuelve a `AUTO`.

## Estructura del repositorio

```
proyecto-tanque-iot-pico2w/
├── main.py        # Programa principal y tareas asyncio
├── config.py      # Credenciales, pines y calibración
├── pio_flow.py    # Contador de pulsos por PIO
├── oled.py        # Driver mínimo SSD1306 (I2C)
└── README.md
```

## Instalación y uso

1. Instalar **MicroPython** para Raspberry Pi Pico 2 W.
2. Copiar `main.py`, `config.py`, `pio_flow.py` y `oled.py` a la placa (por ejemplo, con Thonny).
3. Crear una cuenta en [Adafruit IO](https://io.adafruit.com) y los feeds: `nivel`, `caudal`, `litros`, `bomba`, `alerta` y `modo`.
4. Editar `config.py` con tu red Wi-Fi (**2.4 GHz**, la Pico no soporta 5 GHz), tu usuario y tu clave de Adafruit IO.
5. Calibrar:
   - `TANQUE_LLENO_CM` y `TANQUE_VACIO_CM`: medir con regla la distancia sensor → agua con el tanque lleno y vacío.
   - `PULSOS_POR_LITRO`: verter 1 L real por el caudalímetro y contar los pulsos.
6. Reiniciar la placa. El sistema arranca automáticamente con `main.py`.

> **Seguridad:** no publiques en el repositorio tu `AIO_KEY` ni tu contraseña Wi-Fi. Deja valores de ejemplo en `config.py` antes de subirlo.

## Autores

*Nombres de los integrantes del grupo*
- Rojas Loayza Marcela Andrea
- Monteverde Maravi Celery Lindsay
- Sánchez Mariño Silena Nayrim
- Perez Quiñones Joaquin Principe

Curso: Arquitectura del Computador I, 2026-2
