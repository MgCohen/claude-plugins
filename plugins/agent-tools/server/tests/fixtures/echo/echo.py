import json
import os
import sys
import time

cmd = sys.argv[1]
if cmd == "fail":
    print("something broke", file=sys.stderr)
    sys.exit(3)
if cmd == "sleep":
    time.sleep(5)
print(json.dumps({"argv": sys.argv[1:], "secret": os.environ.get("ECHO_SECRET"),
                  "other": os.environ.get("ECHO_OTHER")}))
