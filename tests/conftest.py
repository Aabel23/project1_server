"""Cho test import được gói `server` dù chạy pytest từ thư mục nào.

Gốc repo là thư mục chứa `tests/`. Chạy từ thư mục cha (`InternProj`) thì
`server` có thể bị hiểu nhầm là thư mục gốc repo; chèn gốc repo lên đầu
sys.path để gói thật `server/server/` (có `__init__.py`) được chọn.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPIKE_DIR = REPO_ROOT / "spike"
VECTOR_DIR = REPO_ROOT / "tests" / "vectors"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
