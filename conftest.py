"""Put the project root on sys.path so `import fof` works under pytest."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fof._compat import ensure_utf8_stdio

ensure_utf8_stdio()
