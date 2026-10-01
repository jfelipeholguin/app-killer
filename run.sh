#!/bin/bash
export PATH="$HOME/android-sdk/platform-tools:$PATH"
cd /home/jholguin/app-killer

# Si el servidor ya está escuchando en el puerto 8085, solo abrir el navegador
if ss -tulpn | grep -q ":8085 "; then
    xdg-open "http://localhost:8085"
    exit 0
fi

# Iniciar app_manager en segundo plano
python3 /home/jholguin/app-killer/app_manager.py &
APP_PID=$!

# Esperar a que el puerto esté activo
for i in $(seq 1 10); do
    if ss -tulpn | grep -q ":8085 "; then
        break
    fi
    sleep 0.3
done

# Abrir el navegador
xdg-open "http://localhost:8085"

# Mantener el proceso activo
wait $APP_PID
