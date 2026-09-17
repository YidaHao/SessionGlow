"""Session snapshots, main/child aggregation and small local history cache."""

import json
import math
import time
from pathlib import Path


STATES = {"unknown", "running", "waiting", "failed", "done"}


class SessionStore:
    def __init__(self, cache=None):
        self.cache = Path(cache) if cache else None
        self.sessions = {}
        self.instances = {}
        self.dirty = False
        if self.cache:
            try:
                rows = json.loads(self.cache.read_text())
                for raw in rows if isinstance(rows, list) else []:
                    row = self.validate(raw)
                    if row:
                        self.sessions[row["id"]] = row
            except (OSError, ValueError):
                pass

    @staticmethod
    def validate(raw):
        if not isinstance(raw, dict):
            return None
        sid, parent = raw.get("id"), raw.get("parent_id")
        if not isinstance(sid, str) or not 0 < len(sid) <= 128:
            return None
        if parent is not None and (not isinstance(parent, str) or len(parent) > 128 or parent == sid):
            return None
        state = raw.get("state")
        if not isinstance(state, str) or state not in STATES:
            return None
        for key in ("last_started", "updated_at"):
            value = raw.get(key, 0)
            if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value < 1e16:
                return None
        row = {"id": sid, "parent_id": parent, "state": state,
               "last_started": raw.get("last_started", 0), "updated_at": raw.get("updated_at", 0)}
        for key, fallback in (("title", sid[:12]), ("project", ""), ("detail", "")):
            value = raw.get(key, fallback)
            row[key] = " ".join(value.split())[:180] if isinstance(value, str) else fallback
        return row

    def receive(self, body, now=None):
        if not isinstance(body, dict):
            return False
        identifier, sequence, rows = body.get("instance_id"), body.get("sequence"), body.get("sessions")
        if (not isinstance(identifier, str) or not 0 < len(identifier) <= 128
                or type(sequence) is not int or sequence < 0 or not isinstance(rows, list) or len(rows) > 256):
            return False
        previous = self.instances.get(identifier)
        if previous and sequence <= previous["sequence"]:
            return False
        if not previous and len(self.instances) >= 128:
            stamp = now if now is not None else time.monotonic()
            self.instances = {key: value for key, value in self.instances.items() if stamp - value["seen"] < 60}
            if len(self.instances) >= 128:
                return False
        validated = [self.validate(raw) for raw in rows]
        if any(row is None for row in validated):
            return False
        removed = body.get("removed", [])
        if not isinstance(removed, list) or len(removed) > 256 or not all(isinstance(s, str) for s in removed):
            return False
        source = body.get("source", {})
        if not isinstance(source, dict):
            return False
        source = {key: value[:512] for key in ("endpoint", "directory")
                  if isinstance(value := source.get(key), str)}
        pid = body.get("source", {}).get("pid")
        if type(pid) is int and pid > 0:
            source["pid"] = pid
        self.instances[identifier] = {"sequence": sequence, "seen": now if now is not None else time.monotonic(),
                                      "online": body.get("online", True) is True,
                                      "source": source,
                                      "ids": {row["id"] for row in validated}}
        for sid in removed:
            if sid in self.sessions:
                del self.sessions[sid]
                self.dirty = True
        for row in validated:
            old = self.sessions.get(row["id"])
            if old is None or row["updated_at"] >= old["updated_at"]:
                if old:
                    row["last_started"] = max(old["last_started"], row["last_started"])
                if row != old:
                    self.sessions[row["id"]] = row
                    self.dirty = True
        if len(self.sessions) > 512:
            ordered = sorted(self.sessions.values(), key=lambda r: r["updated_at"], reverse=True)
            self.sessions = {r["id"]: r for r in ordered[:512]}
        return True

    def connected_ids(self, now=None):
        now = time.monotonic() if now is None else now
        live = set()
        for item in self.instances.values():
            if item["online"] and now - item["seen"] < 20:
                live.update(item["ids"])
        return live

    def connection_count(self, now=None):
        now = time.monotonic() if now is None else now
        return sum(item["online"] and now - item["seen"] < 20 for item in self.instances.values())

    def sources(self, now=None):
        now = time.monotonic() if now is None else now
        return [dict(item["source"], session_count=len(item["ids"]),
                     age_seconds=round(max(0, now - item["seen"]), 1))
                for item in self.instances.values() if item["online"] and now - item["seen"] < 20]

    def rows(self, limit=5, now=None):
        connected = self.connected_ids(now)
        roots = [r for r in self.sessions.values() if not r["parent_id"]]
        roots.sort(key=lambda r: (-r["last_started"], r["id"]))
        result = []
        for root in roots[:limit]:
            children = []
            for child in self.sessions.values():
                parent = child["parent_id"]
                seen = {child["id"]}
                while parent and parent not in seen:
                    if parent == root["id"]:
                        if child["updated_at"] >= root["last_started"]:
                            children.append(child)
                        break
                    seen.add(parent)
                    parent = self.sessions.get(parent, {}).get("parent_id")
            row = dict(root)
            state = root["state"]
            # Root terminal errors survive idle events. Child failures may be recovered by the parent.
            if state != "failed":
                family = [root] + [r for r in children if r["id"] in connected]
                if any(r["state"] == "waiting" for r in family):
                    state = "waiting"
                    row["detail"] = next((r["detail"] for r in family if r["state"] == "waiting"), "")
                elif any(r["state"] == "running" for r in family):
                    state = "running"
            row.update(state=state, connected=root["id"] in connected,
                       children=sum(r["state"] in ("running", "waiting") and r["id"] in connected for r in children))
            result.append(row)
        return result

    def save(self):
        if not self.cache or not self.dirty:
            return
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        temp = self.cache.with_suffix(".tmp")
        temp.write_text(json.dumps(list(self.sessions.values()), ensure_ascii=False, indent=2))
        temp.replace(self.cache)
        self.dirty = False
