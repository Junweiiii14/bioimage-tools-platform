"""Keep GUI regression windows off the user's desktop, including direct pytest runs."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
