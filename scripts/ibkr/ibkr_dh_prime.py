"""poetry run python -m scripts.ibkr.ibkr_dh_prime"""

import re
import subprocess

path_to_dhparam_cert = "./config/ibkr_certs/dhparam.pem"

result = subprocess.run(
    ["openssl", "dhparam", "-in", path_to_dhparam_cert, "-text"], capture_output=True, text=True
).stdout
match = re.search(r"(?:prime|P):\s*((?:\s*[0-9a-fA-F:]+\s*)+)", result)
print(re.sub(r"[\s:]", "", match.group(1)) if match else "No prime (P) value found.")
