"""Persistent JSON-lines client for the local FireRed/LeafGreen (Gen 3) Showdown adapter."""

import json
from pathlib import Path
import select
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[3]
BRIDGE = REPO / "engines" / "frlg-showdown"


class Engine:
    """One Node process; Python owns policies and experimental control."""

    def __enter__(self):
        node = shutil.which("node")
        if not node or not (BRIDGE / "node_modules" / "pokemon-showdown").is_dir():
            raise RuntimeError("Install Node 22+ and run: npm ci --omit=optional --prefix engines/frlg-showdown")
        self.process = subprocess.Popen([node, str(BRIDGE / "runner.cjs")], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, text=True, bufsize=1)
        return self

    def request(self, **message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        if not select.select([self.process.stdout], [], [], 60)[0]:
            raise RuntimeError("Showdown bridge timed out after 60 seconds")
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Showdown bridge exited unexpectedly")
        response = json.loads(line)
        if not response.get("ok"):
            raise RuntimeError("Showdown bridge: " + response.get("error", "unknown error"))
        return response["state"]

    def __exit__(self, *args):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdout.close()
