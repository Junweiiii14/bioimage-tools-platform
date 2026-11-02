"""Reproduce the observed qWait/nested-loop difference in a new workspace."""

import logging
import sys

from bioimage_app.storage import AsyncStorage, StorageCommand
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from PySide6.QtTest import QTest

logging.basicConfig(level=logging.DEBUG)
app = QCoreApplication([])
port = AsyncStorage()
replies = []
closed = []
port.replied.connect(replies.append)
port.closed.connect(lambda: closed.append(True))
port.submit(StorageCommand("create", path=sys.argv[1]))
QTest.qWait(1500)
print("qWait replies", len(replies), flush=True)
loop = QEventLoop()
QTimer.singleShot(1500, loop.quit)
loop.exec()
print("nested loop replies", len(replies), flush=True)
port.shutdown()
loop = QEventLoop()
port.closed.connect(loop.quit)
QTimer.singleShot(10000, loop.quit)
loop.exec()
print("closed", closed, flush=True)
assert closed
