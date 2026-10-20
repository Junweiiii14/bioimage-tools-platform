python
import json
import os
from pathlib import Path
import gdb

def record_owned_inferior(event):
    destination = Path(os.environ["BIOIMAGE_NATIVE_PID_FILE"])
    if not destination.exists():
        destination.write_text(json.dumps({"debugger": os.getpid(), "inferior": gdb.selected_inferior().pid}))

gdb.events.new_thread.connect(record_owned_inferior)
end
