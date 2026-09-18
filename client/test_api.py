import sys
from pathlib import Path

CLIENT_DIR = Path(__file__).resolve().parent
if str(CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(CLIENT_DIR))

from api.client import check_server, get_history

online = check_server()
print(f"Status do Servidor: {'ONLINE' if online else 'OFFLINE'}")
if online:
    resultado = get_history()
    print(f"Histórico ({len(resultado) if isinstance(resultado, list) else 0} registros):")
    print(resultado)
else:
    print("Para iniciar o servidor: python server/run_server.py")