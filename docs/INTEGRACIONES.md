# Contratos de integración · v0.4

## ROS 2: observación primero

Objetivo inicial de integración: ROS 2 Jazzy en un entorno que disponga de `rclpy`, `sensor_msgs` y `std_msgs`. El trabajo de CI `ros2-jazzy` ejecuta un grafo ROS real con datos sintéticos, usando la imagen oficial `ros:jazzy-ros-base`. Las otras distribuciones y los sensores físicos tienen experimentos de compatibilidad separados.

Después de activar el entorno ROS 2, desde la raíz del proyecto:

```bash
python3 -m rosa.ros2 --db rosa-ros.sqlite3 --user local --robot robot_01
```

| Dirección | Topic | Tipo | Contrato |
|---|---|---|---|
| Entrada | `/rosa/local/robot_01/battery` | `sensor_msgs/msg/BatteryState` | `percentage` entre 0 y 1; desconocidos o NaN se rechazan |
| Entrada | `/rosa/local/robot_01/obstacle` | `std_msgs/msg/Bool` | `true`: obstáculo reportado |
| Entrada | `/rosa/local/robot_01/estop` | `std_msgs/msg/Bool` | `true`: paro reportado |
| Entrada | `/rosa/local/robot_01/position` | `std_msgs/msg/String` | `base`, `linea_1`, `linea_2` o `almacen` |
| Salida | `/rosa/local/robot_01/context` | `std_msgs/msg/String` | Snapshot JSON del contexto, una vez por segundo |

El QoS de batería usa el perfil de sensores de ROS. Las otras entradas usan profundidad 10 con configuración estándar. Debes ajustar QoS, nombres y frecuencias a tus publicadores. Publica continuamente los booleanos, no sólo cuando cambien, o vencerán por diseño. `position` representa una etiqueta registrada: no sustituye TF, odometría ni localización.

Ejemplo de datos artificiales para una futura prueba en ROS:

```bash
ros2 topic pub -r 2 /rosa/local/robot_01/battery sensor_msgs/msg/BatteryState "{percentage: 0.82}"
ros2 topic pub -r 2 /rosa/local/robot_01/obstacle std_msgs/msg/Bool "{data: false}"
ros2 topic pub -r 2 /rosa/local/robot_01/estop std_msgs/msg/Bool "{data: false}"
ros2 topic pub -r 2 /rosa/local/robot_01/position std_msgs/msg/String "{data: base}"
ros2 topic echo /rosa/local/robot_01/context
```

Usa terminales independientes para cada publicador. Las entradas Bool/String heredadas registran recepción local. BatteryState conserva `header.stamp` si existe; la entrada `telemetry` conserva fecha de adquisición y secuencia de todos los hechos. Usa tiempos Unix sincronizados; el tiempo simulado de ROS requiere una conversión explícita. Los namespaces separan nombres, **no autentican publicadores ROS**. Para producción se necesitan mensajes con adquisición y secuencia verificables, autenticación del dominio, políticas de red, límites de velocidad y el sistema de seguridad propio del robot.

Los perfiles del observador tienen modo `observation` y el runtime rechaza ejecutarlos. No hay topic `cmd_vel` ni publicación de trayectorias. Una futura integración con Nav2, MoveIt o un controlador concreto debe ser otro adaptador con acciones ROS, seguimiento, cancelación, watchdog, límites mecánicos y evaluación del riesgo de la aplicación. El paro físico debe actuar independientemente de este software.

## Plataformas externas de agentes

`AgentGateway` implementa un contrato genérico saliente; no conoce marcas, cuentas, bases de datos ni APIs propietarias. El envío requiere una llamada explícita de la aplicación:

```python
import os
from rosa import ContextStore, Scope
from rosa.gateway import AgentGateway

store = ContextStore("rosa-ros.sqlite3")
scope = Scope("local", "robot_01")
gateway = AgentGateway(
    endpoint=os.environ["AGENT_CONTEXT_ENDPOINT"],
    token=os.environ["AGENT_CONTEXT_TOKEN"],
    signing_secret=os.environ["AGENT_SIGNING_SECRET"],
)
snapshot = store.snapshot(scope)
# Transmite únicamente cuando tu aplicación lo autorice.
receipt = gateway.publish(snapshot)
print(receipt)
store.close()
```

El endpoint debe aceptar `POST` HTTPS con un documento `robot.context`, `schema_version: "1.1"`, identificador de evento, usuario, robot, modo, revisión, timestamp y hechos permitidos. No se incluyen texto de órdenes, historial ni secretos. `schemas/context-event.schema.json` documenta la estructura. La firma cubre los bytes JSON exactos recibidos.

Cabeceras:

- `Authorization: Bearer <token>`
- `X-ROSA-Signature: sha256=<HMAC_SHA256(body, signing_secret)>`
- `Idempotency-Key: <event_id>`

El receptor debe autenticar el token, vincularlo al usuario permitido, validar el esquema, verificar la firma con comparación constante, rechazar timestamps fuera de su ventana y deduplicar el identificador. La firma no sustituye esos controles. El emisor no sigue redirecciones. No hay cola de salida, reintentos automáticos ni garantía de entrega; si implementas reintentos, conserva el mismo `event_id` para el mismo evento.

No envíes credenciales desde el navegador. Secreto y token se mantienen en el proceso servidor mediante variables de entorno. La consola sólo permite descargar un JSON: **Exportar contexto** no envía datos a un tercero.

## Recomendaciones entrantes

El SDK incluye `record_advisory(store, scope, {"agent_id": "...", "message": "..."})` para conservar una recomendación después de que el sistema integrador autentique a su emisor. No hay receptor HTTP público implementado. Este método no actualiza sensores, no modifica reglas y no ejecuta tareas.

Para llevar una recomendación a una tarea: el operador la revisa, propone una orden mediante el runtime y confirma la propuesta. Una respuesta de un agente nunca se debe importar como telemetría autorizada.

## API de la consola

| Método y ruta | Función |
|---|---|
| `GET /api/state` | Contexto actual y últimos eventos de `demo/amr_01` |
| `GET /api/export` | Documento de contexto descargable |
| `POST /api/scenario` | Selecciona una condición de prueba |
| `POST /api/plan` | Genera una propuesta con `text` y `provider` |
| `POST /api/execute` | Confirma un `id` y aplica efectos simulados |

Las mutaciones requieren el token por proceso y origen local. Estas rutas son una interfaz de demostración, no una API pública estable ni un servidor multiusuario.

## Telemetría con adquisición y secuencia

La entrada `/rosa/USER/ROBOT/telemetry` usa `std_msgs/msg/String` con este contrato JSON (valores sintéticos):

```json
{"schema_version":"1.0","user_id":"local","robot_id":"robot_01","observed_at":1790640000,"sequence":1,"values":{"battery":82,"obstacle":false,"estop":false,"position":"base"}}
```

Sustituye `observed_at` por la fecha Unix real de adquisición; no copies la fecha de ejemplo como si fuese actual. Cada secuencia debe aumentar y persistir tras reinicios del productor. ROSA rechaza hechos fuera de orden y repeticiones sin renovar su fecha. Se exige el mismo usuario/robot que el observador configurado. El adaptador asigna la fuente `ros2/telemetry`; el mensaje no puede elegir otra fuente.

Para exigir esta ruta, inicia el observador con un perfil:

```bash
python3 -m rosa.ros2 --db rosa-ros.sqlite3 --user local --robot robot_01 --profile examples/observation-profile.json
```

El perfil de ejemplo restringe fuentes y exige adquisición. Los mensajes heredados sin fecha no satisfacen ese requisito. El ejemplo publica datos continuamente, no órdenes a actuadores. Los valores del perfil se deben ajustar a los requisitos medidos de tu robot.

## Reproducir la prueba de integración de CI

Dentro de ROS 2 Jazzy, desde la raíz del repositorio:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=1
python3 tests/integration/ros2_smoke.py
```

El experimento inicia el observador, publica datos sintéticos por DDS y verifica el contexto devuelto. Comprueba que un paquete repetido no borra un obstáculo. No requiere un robot físico ni un modelo local. Consulta el resultado del trabajo `ros2-jazzy` en Actions para la revisión concreta que usarás.

## Diagnóstico rápido

- **No hay contexto:** confirma usuario, robot, namespace, ROS_DOMAIN_ID y QoS; usa `ros2 topic list` y `ros2 topic echo`.
- **Datos vencidos:** revisa frecuencia de adquisición y TTL del perfil; retransmitir el mismo paquete no produce una observación nueva.
- **Fuente rechazada:** revisa `allowed_sources` y la identidad del adaptador autenticado.
- **Secuencia reiniciada:** conserva el contador del sensor; un reinicio no convierte los paquetes viejos en nuevos.
- **Propuesta bloqueada tras cambiar requisitos:** genera una nueva propuesta usando el perfil actualizado.
