# proyecto-tanque-iot-pico2w
Diseño e implementación de un sistema IoT con RaspBerry Pi Pico 2 W para la gestión de tanque elevado y bomba.
Proyecto final del curso Arquitectura del Computador I 2026-2

## Descripción del proyecto
El siguiente proyecto consiste en un sistema embebido IoT desarrollado sobre la plataforma **RaspBerry Pi Pico 2 W** para automatizar el llenado de un tanque elevado, prevenir daños en la electrobomba y monitorear el consumo diario de agua en tiempo real.

## Problema que resuelve
- **Desbordes hídricos:** Detiene automáticamente la electrobomba cuando el nivel del agua alcanza el límite superior, evitando desperdicio hídrico y daños estructurales.
- **Protección contra marcha en seco:** Verifica el flujo real en la tubería mediante un caudalímetro; si la bomba opera sin paso de agua se apaga inmediatamente y emite una alerta.
- **Telemetría y consumo:** Registra los litros consumidos diariamente y envía alertas a la nube ante cortes de suministro o fallas.

## Arquitectura y componentes
* **Microcontrolador:** Raspberry Pi Pico 2 W (RP2350) programado en **MicroPython** con concurrencia cooperativa asyncio.
* **Sensores y actuadores:**
  * **JSN-SR04T:** Sensor ultrasónico impermeable de nivel de agua.
  * **YF-S201:** caudalímetro de efecto Hall.
  * **Electrobomba 12 V DC:** Accionada mediante módulo relé/MOSFET aislado.
* **Reto de arquitectura (PIO):** Implementación de una máquina de estados Programmable I/O (PIO) para realizar el conteo por hardware de los pulsos del caudalímetro YF-S201, liberando al procesador principal ARM Cortex-M33.
* **Conectividad y Nube:** Publicación de telemetría y alertas mediante protocolo MQTT/HTTP en dashboard web.
* **Fabricación 3D:** Tapa de tanque funcional con soporte integrado para el sensor ultrasónico.
