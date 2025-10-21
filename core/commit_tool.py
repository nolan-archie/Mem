



import subprocess

import json

import os

from datetime import datetime

from pathlib import Path

from .simulator import compute_file_diff, SANDBOX_DIR 



LOG_FILE = "../logs/commit.log" 



def log(msg):

    ts = datetime.now().isoformat()

    with open(LOG_FILE, "a") as f:

        f.write(f"{ts} {msg}\n")



def merge(overlay_dir: str, target_dir: str = SANDBOX_DIR) -> Dict:

    if not Path(overlay_dir).exists():

        raise ValueError("Overlay missing")

    if not Path(target_dir).exists():

        raise ValueError("Target missing")

    

    

    diff = compute_file_diff("merge", target_dir)  

    log(f"Pre-merge diff: {json.dumps(diff)}")

    

   

    subprocess.run(["rsync", "-a", "--dry-run", f"{overlay_dir}/", target_dir], check=True, capture_output=True)

    subprocess.run(["rsync", "-a", f"{overlay_dir}/", target_dir], check=True)

    

    log("Merge done")

    return {"ok": True, "merged": target_dir}
