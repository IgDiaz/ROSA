# ROSA · v0.3.1 experimental

**Robotics Operational Systems and Agave**, un proyecto abierto de CDT. El agave conecta la identidad con Guadalajara y Jalisco. Código original bajo licencia MIT, copyright © 2026 CDT.

**Contexto en movimiento.** Un kit abierto para crear aplicaciones robóticas que interpretan una orden, consultan el estado del robot y explican si pueden realizarla. Lanzamiento Minerva; nombres inspirados en Guadalajara y su región.

La entrega contiene librerías Python originales, una consola visual y un robot simulado. Está pensada como una capa sobre ROS 2. ROS ya es un ecosistema de herramientas y librerías; este proyecto no implementa un kernel, una distribución de sistema operativo ni reemplaza sus drivers, navegación o middleware.

## Arranque en un minuto

Requisito: Python 3.11 o posterior. El simulador usa únicamente la biblioteca estándar; no necesita instalar dependencias ni conectarse a Internet.

1. Descomprime el paquete.
2. En Windows, abre **iniciar-demo.bat**. Alternativamente, abre una terminal dentro de `ROSA` y ejecuta:

   ```powershell
   python -m rosa
   ```

3. Abre **http://127.0.0.1:8765** en tu navegador.
4. Escribe **Inspecciona línea 2**, pulsa **Proponer** y después **Confirmar simulación**.
5. Selecciona **Batería baja** y repite la orden. Ahora se bloquea y se sugiere proponer el regreso a la base.

En macOS o Linux: `python3 -m rosa`. Para cerrar, `Ctrl+C` en la terminal. La memoria se conserva en `rosa-demo.sqlite3`, junto al proyecto. Para una sesión efímera usa `python -m rosa --db :memory:`. Si el puerto está ocupado, añade `--port 8770` y usa ese puerto en el navegador.

El mapa es una visualización de estados: el desplazamiento y la inspección se aplican como cambios discretos simulados. No existe simulación física, medición de defectos ni un motor de navegación detrás de la animación.

## Cinco módulos reutilizables

| Módulo | Implementado en esta versión | Punto de extensión |
|---|---|---|
| Context | Identidad `user_id / robot_id`; hechos con fuente, fecha, confianza y vigencia; revisión de contexto; memoria SQLite | Perfil por tipo de robot, unidades y nuevas observaciones |
| Commands | Intención estructurada; cinco tareas; reglas; confirmación; expiración; repetición idempotente | Catálogo de habilidades y adaptadores de ejecución |
| Local AI | Intérprete por reglas sin LLM; adaptador para Ollama con esquema JSON y validación local | Un modelo local instalado por el usuario |
| ROS 2 | Observador de batería, obstáculo, paro y posición; publica contexto JSON | Integración específica del robot y mensajes ROS tipados |
| Agent Gateway | Exportación explícita HTTPS con token, firma HMAC e identificador de evento; registro de recomendaciones | Endpoint privado de una plataforma de agentes |

`policy.py` mantiene las reglas deterministas y `runtime.py` coordina la propuesta y la simulación. No hay una plataforma externa conectada por defecto ni transmisión automática de información.

## Una demostración que se puede comprobar

| Escenario | Orden | Resultado esperado |
|---|---|---|
| Normal | Inspecciona línea 2 | Propuesta lista; confirmar cambia posición y descuenta 3 puntos de batería simulada |
| Batería baja, 14 % | Inspecciona línea 2 | Bloqueada; recomienda proponer regreso a base |
| Batería baja, 14 % | Vuelve a la base | Lista; sólo simula el trayecto, no recarga la batería |
| Obstáculo | Inspecciona línea 2 | Bloqueada |
| Paro activo | Inspecciona línea 2 | Bloqueada |
| Sin telemetría, esperar más de 3 segundos | Inspecciona línea 2 | Bloqueada por evidencia vencida |
| Cualquier escenario | Haz algo increíble | Solicita aclarar la tarea en modo reglas |

También funcionan `Ve a almacén`, `Ve a línea 1`, `Detente` y `Estado`. La gramática sin LLM es deliberadamente limitada y rechaza tareas compuestas. El botón de paro es una entrada del simulador, no un paro de emergencia físico.

## Usarlo como librería

Desde la raíz del proyecto, sin instalar:

```python
from rosa import ContextStore, Scope, Runtime

store = ContextStore("mi-robot.sqlite3")
robot = Scope("mi_organizacion", "robot_01")
store.register(robot, mode="simulation")
store.observe(robot, {
    "battery": 82, "obstacle": False,
    "estop": False, "position": "base"
}, source="simulator")

runtime = Runtime(store)
plan = runtime.propose(robot, "Inspecciona línea 2")
print(plan["status"], plan["reason"])
# Tras una confirmación explícita del operador:
if plan["status"] == "ready":
    print(runtime.execute_simulation(robot, plan["id"]))
store.close()
```

Opcionalmente, `python -m pip install .` permite importarlo desde otros proyectos y usar el comando `rosa`. La instalación puede descargar herramientas de construcción; no hace falta para la demostración. `rosa-robotics-kit` es el nombre del paquete local, no una afirmación de que esté publicado en PyPI.

## IA local opcional

Instala y arranca Ollama por tu cuenta. Escoge un modelo que funcione en tu equipo y cuya licencia se ajuste al uso previsto. Consulta `ollama list` para obtener su nombre exacto. Después:

```powershell
python -m rosa --ollama-model TU_MODELO_INSTALADO
```

Selecciona **Ollama** en la consola. El adaptador usa `http://127.0.0.1:11434/api/chat`, solicita JSON estructurado y vuelve a validarlo. El modelo recibe la orden, el contexto actual y hasta cinco eventos recientes del mismo robot. No se entrena, no modifica políticas, no genera programas ejecutables y no tiene herramientas de shell.

El esquema no garantiza que la interpretación semántica sea correcta. La consola muestra la acción propuesta antes de confirmarla. Si Ollama falla, se informa el error; no se cambia silenciosamente de proveedor. El adaptador sólo admite loopback literal, desactiva proxies para esa llamada y rechaza redirecciones.

## Context awareness: alcance real

Esta v0.3.1 convierte contexto operativo en decisiones verificables: identidad, capacidades, estado, procedencia, edad de evidencia y eventos recientes. Las decisiones conservan la evidencia utilizada. La confianza es una entrada del adaptador; **no es una probabilidad calibrada ni una garantía de seguridad**.

Las cuatro observaciones tienen esquema fijo. Obstáculo y paro vencen a los 3 segundos; batería y posición a los 10. Se exige confianza de al menos 0.8 para desplazamientos. Las tareas normales requieren 20 % de batería y el regreso a base 8 %. Son parámetros de demostración, no límites certificados o dimensionados para un robot concreto.

Las propuestas vencen a los 30 segundos. Se revisa de nuevo el contexto al ejecutarlas. Cambiar un valor, su fuente o su confianza incrementa la revisión y vuelve obsoletas las propuestas anteriores. Un heartbeat con idéntico contenido actualiza la fecha sin invalidarlas. Las muestras anteriores a la última aceptada se ignoran.

Todavía no hay fusión multisensor, detección visual, navegación espacial, predicción de fallas, planificación jerárquica ni aprendizaje continuo. No se ha demostrado una mejora frente a ROS 2, ni se presenta este prototipo como investigación novedosa.

## Conectar ROS 2 y una plataforma de agentes

Consulta [docs/INTEGRACIONES.md](INTEGRACIONES.md) para los contratos, ejemplos de telemetría, firma y recepción de recomendaciones. La v0.3.1 observa ROS 2 y publica contexto; no envía órdenes a motores. La integración con una plataforma concreta requiere implementar o acordar su endpoint receptor y autenticación.

La consola sólo atiende en loopback, con comprobación de Host, origen y token por proceso para las mutaciones. Es un servidor de desarrollo para un operador local. La separación de datos por `Scope` en el SDK no equivale a autenticación ni autorización multiusuario; el sistema que lo incorpore debe resolverlas.

## Verificación y próximos pasos

```powershell
python -m unittest discover -s tests -v
```

Consulta [docs/VALIDACION.md](VALIDACION.md) para lo probado y las limitaciones. [docs/ROADMAP.md](ROADMAP.md) propone una ruta corta hacia un piloto medible con un robot.

## Licencia y referencias

Código original bajo [MIT](../LICENSE): permite uso, modificación y distribución, incluso comercial, conservando el aviso. El texto MIT existente se mantiene intacto. [LICENSE-CDT](../LICENSE-CDT) añade por separado la licencia de las aportaciones originales de CDT, con los mismos términos MIT, sin restricciones adicionales y sin sustituir licencias ni avisos de terceros.

ROS y ROS 2 tienen licencias distintas según el componente; no les atribuimos una licencia MIT general. Sus paquetes, las demás dependencias y los modelos de IA conservan sus propias licencias y avisos. Consulta [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). No se incluyen binarios ni código copiado de ROS u Ollama; no existe afiliación o aprobación de esos proyectos.

Este repositorio público contiene el SDK, adaptadores, esquemas, ejemplos, pruebas y consola local de simulación. La consola es una herramienta funcional del SDK; la landing, su servidor público y la configuración de hosting se mantienen en otro repositorio. La web consume una versión fija de este SDK.

Consulta el [aviso de privacidad y tratamiento de datos](../PRIVACY.md) y la [política de seguridad](../SECURITY.md).

Referencias consultadas el 28 de septiembre de 2026:

- [ROS](https://www.ros.org/) — referencia solicitada; la portada bloqueó la lectura automatizada.
- [ROS 2, organización oficial](https://github.com/ros2) — descripción del ecosistema de librerías y herramientas.
- [ROS 2 Actions, diseño oficial](https://design.ros2.org/articles/actions.html) — acciones con resultados y seguimiento, para una futura ejecución física.
- [Ollama, structured outputs](https://docs.ollama.com/capabilities/structured-outputs) — formato JSON con esquema.
- [Ollama, API chat](https://docs.ollama.com/api/chat) — contrato HTTP usado por el adaptador.

La arquitectura del kit, los umbrales de prueba y la hoja de ruta son decisiones de este prototipo, no recomendaciones oficiales de ROS u Ollama.
