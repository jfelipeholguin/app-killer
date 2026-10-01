# App Killer

Herramienta web para detectar la app en primer plano en tu Android vía ADB y desinstalarla con un clic.

## Requisitos

- Python 3
- ADB instalado y accesible en el PATH, o en `~/android-sdk/platform-tools/adb`
- `aapt2` (viene con el SDK de Android, en `build-tools/*/aapt2`) para resolver el nombre real de las apps
- Dispositivo Android conectado con depuración USB activada

## Uso

```bash
./run.sh
```

O directamente:

```bash
python3 app_manager.py
```

Abrí `http://localhost:8085` en tu navegador. La app que tengas abierta en el teléfono aparecerá automáticamente.

También hay un lanzador de escritorio (`app-killer.desktop`) que se puede instalar copiándolo a `~/.local/share/applications/`.

## Cómo funciona

- Detecta la app en primer plano usando `dumpsys activity activities` (`topResumedActivity` en Android 10+, con fallback a `dumpsys window`)
- Muestra nombre real, versión y tipo (sistema/usuario)
- Desinstala apps de usuario con `adb uninstall` y apps de sistema con `pm uninstall --user 0`

### Nombre real de las apps

Android 10+ ya no expone el campo `label` en `dumpsys package` (solo un `labelRes` numérico que no se puede resolver a texto), por eso el nombre se lee del APK con `aapt2 dump badging`. Los APK se descargan una sola vez a `~/.cache/app-killer/apks/` y se reutilizan entre reinicios; si `aapt2` no está disponible, la UI cae al nombre del paquete.

## Notas de seguridad

El servidor escucha **solo en `127.0.0.1`** y rechaza cualquier petición cuyo `Host` no sea `localhost`/`127.0.0.1` o cuyo `Origin` no sea el propio servidor. Sin esto, cualquier página web abierta en el navegador podría llamar a la API local y desinstalar apps del teléfono sin que hagas nada.

## Licencia

MIT