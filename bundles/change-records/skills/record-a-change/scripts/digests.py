"""Print {path: sha256} for the given files, CRLF read as LF -- the digests a change record states."""
import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    data = path.read_bytes()
    try:
        data = data.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    except UnicodeDecodeError:
        pass
    return hashlib.sha256(data).hexdigest()


print(json.dumps({p: (digest(Path(p)) if Path(p).is_file() else "DELETED") for p in sys.argv[1:]}, indent=2))
