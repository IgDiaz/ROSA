# Evolución continua hacia sistemas robóticos industriales avanzados

## Hipótesis

Un operador puede pedir una tarea sin conocer topics o scripts, mientras un contexto con fecha, fuente e identidad evita ejecutar órdenes cuando faltan condiciones verificables. El resultado debe medirse antes de afirmar que el robot es más inteligente, más seguro o más productivo.

## Base disponible

Un robot simulado, cuatro señales de contexto, cinco acciones, una consola conversacional, memoria persistente, adaptador de IA local y contratos de integración. Un solo paquete modular reduce configuración para empezar.

## 0.4: requisitos verificables y compatibilidad

Perfiles por robot, fecha de adquisición y recepción, secuencias persistentes, migración aditiva, pruebas de concurrencia, referencia de API y CI con ROS 2 Jazzy. Cada incremento publica sus criterios y resultados.

## Siguiente experimento: un robot observado

Elegir un AMR o un robot educativo que ya tenga drivers ROS 2 funcionando. Conectar datos reales en modo observación, acordar fuentes confiables y registrar tiempos de adquisición. Repetir los escenarios sin controlar movimiento. Criterio de aceptación: ninguna observación ausente, vieja o del robot equivocado se toma como evidencia válida.

## Después: una sola habilidad real

Integrar una habilidad limitada mediante una acción ROS con cancelación y resultado: por ejemplo, desplazamiento entre dos puntos ya mapeados en un entorno de pruebas. Confirmación humana, controlador existente, velocidad acotada y paro físico independiente. La habilitación de movimiento físico tendrá criterios de aceptación específicos del robot, pruebas de fallo y validación independiente del sistema completo.

## Medir antes de ampliar

Probar el mismo conjunto de órdenes y estados con el flujo actual del robot y con la nueva interfaz. Registrar:

- Porcentaje de intenciones interpretadas correctamente, separando reglas y modelo local.
- Órdenes ambiguas detectadas y preguntas de aclaración.
- Tareas bloqueadas por evidencia ausente/vencida y bloqueos innecesarios.
- Latencia mediana y percentil 95, tiempo del operador y correcciones manuales.
- Memoria, CPU, energía y tasa de fallos del modelo local en el equipo elegido.

Un umbral de piloto propuesto: cero ejecuciones en los escenarios negativos del conjunto de pruebas, con trazabilidad completa de cada propuesta. Esto sólo acredita ese conjunto, no seguridad general ni certificación.

## Aportación diferenciadora a desarrollar

Convertir contexto operativo verificable en un contrato portable entre robots y agentes, con una experiencia que una persona de planta pueda usar. La investigación posterior puede estudiar antigüedad de contexto, calidad de decisiones y costo económico. La arquitectura ampliará sus contratos a medida que los pilotos industriales aporten requisitos y evidencia.
