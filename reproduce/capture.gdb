set pagination off
set confirm off
set python print-stack full
set architecture i386:x86-64
set osabi GNU/Linux
set remotetimeout 30
python
import os
from pathlib import Path
lab = Path(os.environ["VL_CLASSROOM"]).resolve()
os.environ["VL_CLASSROOM"] = str(lab)
Path(os.environ["CAPTURE_DIR"]).mkdir(parents=True, exist_ok=True)
end
target remote 127.0.0.1:26002
source scripts/gdb/macros.gdb
source visualinux-gdb.py
python
script = lab / "stages.py"
exec(compile(script.read_bytes(), str(script), "exec"))
end
detach
