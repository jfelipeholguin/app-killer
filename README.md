# App Killer

Herramienta web para detectar la app en primer plano en tu Android vía ADB y desinstalarla con un clic.

## Requisitos

- Python 3
- ADB instalado y en el PATH
- Dispositivo Android conectado con depuración USB activada

## Uso

```bash
python3 app_manager.py
```

Abrí `http://localhost:8080` en tu navegador. La app que tengas abierta en el teléfono aparecerá automáticamente.

## Cómo funciona

- Detecta la app en primer plano usando `dumpsys window` y `dumpsys activity`
- Muestra nombre real, versión y tipo (sistema/usuario)
- Desinstala apps de usuario con `adb uninstall` y apps de sistema con `pm uninstall --user 0`
- UI auto-recargable cada 5 segundos, diseño responsive

## Licencia

MIT
