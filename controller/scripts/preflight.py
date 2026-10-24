"""Check that no older Bridge owns the endpoint before lengthy backup/flashing."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
from ipc_path import acquire_endpoint
try:
    lease=acquire_endpoint();lease.close()
except Exception as error:
    sys.exit(str(error))
