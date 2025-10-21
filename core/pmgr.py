                                                                                                                                   



"""
Permissions manager (PMgr).
- Enforces sandbox-only file access.
- Requires explicit approvals for risky ops via ephemeral tokens.
- Uses config/permissions.json for allowed/disallowed lists.
"""



import json

import os

import secrets

import time

from pathlib import Path

from typing import Dict, Optional

from .utils.logging import log_action



PERM_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "permissions.json"

APPROVALS_PATH = Path(__file__).resolve().parents[1] / "config" / "approvals.json"

DEFAULT_SANDBOX = str(Path.home() / "MainmiData")



def _load_json(path: Path, default):

    try:

        with open(path, "r", encoding="utf-8") as f:

            return json.load(f)

    except FileNotFoundError:

        return default



_EPHEMERAL_APPROVALS: Dict[str, Dict] = {}



class PMgr:

    def __init__(self, config_path: Path = PERM_CONFIG_PATH):

        self.config_path = config_path

        self.config = _load_json(self.config_path, {

            "sandbox_only": True,

            "sandbox_dir_default": DEFAULT_SANDBOX,

            "allowed_actions_in_sandbox": [],

            "disallowed_actions": [],

            "prompt_required_for": [],

            "ephemeral_token_policy": {"enabled": True, "default_ttl_seconds": 600}

        })



    def reload(self):

        self.config = _load_json(self.config_path, self.config)



    @property

    def sandbox_dir(self) -> str:

        return self.config.get("sandbox_dir_default", DEFAULT_SANDBOX)



    def is_path_in_sandbox(self, path: str) -> bool:

        try:

            p = Path(path).expanduser().resolve()

            sandbox = Path(self.sandbox_dir).expanduser().resolve()

            return sandbox == p or sandbox in p.parents

        except Exception:

            return False



    def authorize(self, action: str, path: Optional[str] = None) -> bool:

        if self.config.get("sandbox_only", True) and path:

            if not self.is_path_in_sandbox(path):

                return False

        if action in self.config.get("disallowed_actions", []):

            return False

        if action in self.config.get("prompt_required_for", []):

            return False

        return True



    def request_approval(self, action: str, reason: str, ttl: Optional[int] = None) -> str:

        ttl = ttl or int(self.config.get("ephemeral_token_policy", {}).get("default_ttl_seconds", 600))

        token = secrets.token_urlsafe(24)

        _EPHEMERAL_APPROVALS[token] = {"action": action, "reason": reason, "expires": time.time() + ttl, "approved": False}

        log_action("pmgr_request", {"action": action, "reason": reason, "token": token})

        self._persist_approvals()

        return token



    def approve(self, token: str) -> bool:

        info = _EPHEMERAL_APPROVALS.get(token)

        if not info:

            log_action("pmgr_deny", {"token": token, "reason": "not_found"}, "warn")

            return False

        if time.time() > info["expires"]:

            _EPHEMERAL_APPROVALS.pop(token, None)

            log_action("pmgr_deny", {"token": token, "reason": "expired"}, "warn")

            return False

        info["approved"] = True

        log_action("pmgr_approve", {"token": token, "action": info["action"]})

        self._persist_approvals()

        return True



    def check_approval(self, token: str) -> bool:

        info = _EPHEMERAL_APPROVALS.get(token)

        if not info:

            return False

        if time.time() > info["expires"]:

            _EPHEMERAL_APPROVALS.pop(token, None)

            return False

        return bool(info.get("approved", False))



    def _persist_approvals(self):

        try:

            APPROVALS_PATH.parent.mkdir(parents=True, exist_ok=True)

            with open(APPROVALS_PATH, "w", encoding="utf-8") as f:

                json.dump(_EPHEMERAL_APPROVALS, f, indent=2)

        except Exception:

            pass



pmgr = PMgr()
