"""Fetch one hash-pinned official Windows x64 API wheel into ignored target/.

No model weights are downloaded. Run this only during explicitly authorized
development provisioning, then install offline into a local Python 3.10+ venv.
"""

import hashlib
from pathlib import Path
import urllib.request

FILENAME = "litert_lm_api-0.18.1-py3-none-win_amd64.whl"
URL = "https://files.pythonhosted.org/packages/a2/86/ccc1ca0c26ff1aa7e812800964bb510a1dd376e38c03526d0939173e8911/" + FILENAME
SHA256 = "2c786288b0e41291e52a611a51a6ab6ec755a3196b86c60d5269779010042895"
SIZE = 26403799


def main():
    root = Path(__file__).resolve().parents[3]
    destination = root / "target" / "litert-spike" / FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        payload = destination.read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=60) as response:
            payload = response.read(SIZE + 1)
    if len(payload) != SIZE or hashlib.sha256(payload).hexdigest() != SHA256:
        raise SystemExit("Official wheel size/hash mismatch; nothing installed.")
    destination.write_bytes(payload)
    print(f"Verified {FILENAME}: {SIZE} bytes; SHA256 {SHA256}")


if __name__ == "__main__":
    main()
