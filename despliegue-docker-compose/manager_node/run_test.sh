#!/bin/bash
echo "🚀 Ejecutando tests con pytest en el contenedor Docker..."
docker compose -f ../docker-compose.yml run --rm manager pytest "$@"
echo "✅ Tests completados."

### Uso:
# Guarda este script como run_test.sh y dale permisos de ejecución:
# chmod +x run_test.sh
# Luego, puedes ejecutarlo con:
# ./run_test.sh
# Puedes pasar argumentos adicionales a pytest, por ejemplo:
# ./run_test.sh -v tests/test_example.py
# Esto ejecutará pytest con el archivo de prueba especificado.
# Asegúrate de que Docker y Docker Compose estén instalados y configurados correctamente.
# Este script asume que tienes un servicio llamado 'api' en tu docker-compose.yml