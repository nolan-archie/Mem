                                                                                                                                                                                                                                                



import difflib

import subprocess

import os

import json

from pathlib import Path

from typing import Dict, Optional



PERM_JSON = "../config/permissions.json"                

SANDBOX_DIR = json.loads(Path(PERM_JSON).read_text())["sandbox_dir"]



def compute_text_diff(before: str, after: str, label: str = "change") -> str:

    diff = difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile=f"before_{label}", tofile=f"after_{label}")

    return "\n".join(diff)



def snapshot_dir() -> str:

    snap_dir = f"/tmp/mainmi_snap_{os.getpid()}"

    subprocess.run(["cp", "-r", SANDBOX_DIR, snap_dir], check=True)

    return snap_dir



def compute_file_diff(action: str, target: str, new_content: Optional[str] = None) -> Dict:

    if not Path(target).is_relative_to(SANDBOX_DIR):

        raise ValueError("Target outside sandbox")

    

    rel = str(Path(target).relative_to(SANDBOX_DIR))

    snap = snapshot_dir()

    snap_target = f"{snap}/{rel}"

    

    if action == "modify_file":

        with open(snap_target, "w") as f:

            f.write(new_content or "")

    

    try:

        r = subprocess.run(["diff", "-u", "--recursive", snap, SANDBOX_DIR], capture_output=True, text=True)

        diff_str = r.stdout if r.returncode else "No changes"

    finally:

        subprocess.run(["rm", "-rf", snap])

    

    return {"diff_id": f"diff_{os.urandom(4).hex()}", "diff": diff_str, "target": target}
