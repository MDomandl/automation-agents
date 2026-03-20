from pathlib import Path
from typing import Dict, Any

import tomllib  # Python 3.11


class ConfigLoader:
    def load(self, path: Path) -> Dict[str, Any]:
        with path.open("rb") as f:
            return tomllib.load(f)