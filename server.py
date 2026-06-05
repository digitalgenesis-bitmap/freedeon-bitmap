from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone
import json
import os

PORT = 8000
STATE_FILE = "state.json"

VALID_CHAINS = {"bitmap", "bitcoin", "local", "intermesh", "tap"}

DEFAULT_ANCHOR = {
    "type":    "anchor",
    "label":   "freedeon.bitmap",
    "chain":   "bitmap",
    "ref":     "freedeon.bitmap",
    "status":  "declared",
    "details": {}
}


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}
    else:
        data = {}

    data.setdefault("memory",    [])
    data.setdefault("identity",  {"version": "v0.3"})
    data.setdefault("knowledge", {})
    data.setdefault("activity",  [])
    data.setdefault("anchors",   [])

    # ── bootstrap next_id ───────────────────────────────────────────────────
    if "next_id" not in data:
        highest = 0
        for col in ("memory", "activity", "anchors"):
            for entry in data[col]:
                if isinstance(entry, dict):
                    highest = max(highest, entry.get("id", 0))
        data["next_id"] = highest + 1

    # ── auto-create default anchor on first run only ─────────────────────────
    anchor_ever_created = any(
        isinstance(e, dict) and e.get("action") == "anchor_create"
        for e in data["activity"]
    )
    if not data["anchors"] and not anchor_ever_created:
        anchor_id = data["next_id"]
        data["next_id"] += 1
        anchor = {**DEFAULT_ANCHOR,
                  "id":         anchor_id,
                  "created_at": now_utc()}
        data["anchors"].append(anchor)
        data["primary_anchor_id"] = anchor_id
        data["activity"].append({
            "id":         data["next_id"],
            "created_at": now_utc(),
            "action":     "anchor_create",
            "input":      "freedeon.bitmap",
            "ref_id":     anchor_id,
            "status":     "ok",
            "details":    {"label": "freedeon.bitmap",
                           "chain": "bitmap",
                           "auto":  True}
        })
        data["next_id"] += 1

    # ── primary_anchor_id consistency check ──────────────────────────────────
    active_anchors = [
        a for a in data["anchors"]
        if isinstance(a, dict) and a.get("status") != "revoked"
    ]
    active_ids = {a["id"] for a in active_anchors}
    pid = data.get("primary_anchor_id")

    if pid is None or pid not in active_ids:
        if active_anchors:
            fallback = min(active_anchors, key=lambda a: a["id"])
            data["primary_anchor_id"] = fallback["id"]
            print(f"[Freedeon] WARNING: primary_anchor_id repaired → {fallback['id']}")
        else:
            data["primary_anchor_id"] = None
            print("[Freedeon] WARNING: no active anchors. primary_anchor_id is null.")

    return data


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


state = load_state()


def alloc_id():
    nid = state["next_id"]
    state["next_id"] = nid + 1
    return nid


def record_activity(action, input_text=None, ref_id=None,
                    details=None, entry_type=None):
    entry = {
        "id":         alloc_id(),
        "created_at": now_utc(),
        "action":     action,
        "input":      input_text,
        "ref_id":     ref_id,
        "status":     "ok"
    }
    if entry_type is not None:
        entry["type"] = entry_type
    if details is not None:
        entry["details"] = details
    state["activity"].append(entry)


def find_memory_by_id(target_id):
    for entry in state.get("memory", []):
        if isinstance(entry, dict) and entry.get("id") == target_id:
            return entry
    return None


def find_anchor_by_id(target_id):
    for entry in state.get("anchors", []):
        if isinstance(entry, dict) and entry.get("id") == target_id:
            return entry
    return None


def get_primary_anchor():
    pid = state.get("primary_anchor_id")
    if pid is None:
        return None
    return find_anchor_by_id(pid)


def get_checkpoints():
    return [
        e for e in state.get("activity", [])
        if isinstance(e, dict) and e.get("type") == "checkpoint"
    ]


def anchor_label_exists(label):
    return any(
        isinstance(a, dict) and a.get("label") == label
        for a in state.get("anchors", [])
    )


def handle_command(raw_command):
    parts = raw_command.strip().split(None, 1)
    command = parts[0].lower() if parts else ""
    argument = parts[1] if len(parts) > 1 else ""

    # ── READ-ONLY COMMANDS ───────────────────────────────────────────────────

    if command == "help":
        return (
            "Commands: help | status | memory | memory all | territory | signal | "
            "remember <text> | forget <id> | checkpoint <id> | checkpoints | "
            "set <key> <value> | identity | profile | log | "
            "anchor create <label> | anchor list | anchor primary <id> | "
            "anchor resolve | anchor revoke <id>. "
            "You are sovereign. The mesh is live."
        )

    if command == "status":
        return (
            "Freedeon node: ACTIVE. "
            "Chain: intact. "
            "Signal: strong. "
            "Sovereignty: non-negotiable."
        )

    if command == "territory":
        identity = state.get("identity", {})
        t = identity.get("territory", "").strip()
        if t:
            return f"Territory: {t}. Defined by signal, not borders."
        return (
            "Territory is undefined. "
            "Use: set territory <name>. "
            "Broadcast. Expand. Hold the mesh."
        )

    if command == "memory":
        memories = state.get("memory", [])
        show_all = argument.strip().lower() == "all"
        if not memories:
            return "Memory is empty. The mesh has not been written yet."
        lines = []
        for entry in memories:
            if isinstance(entry, dict):
                if entry.get("deleted") and not show_all:
                    continue
                eid    = entry.get("id", "?")
                ts     = entry.get("created_at", "")[:16].replace("T", " ")
                text   = entry.get("content", "")
                marker = " [deleted]" if entry.get("deleted") else ""
                lines.append(f"[{eid}] {ts}  {text}{marker}")
            else:
                lines.append(f"[-] {entry}")
        if not lines:
            return "No active memories. Use 'memory all' to include deleted entries."
        header = "Stored memories (including deleted):" if show_all else "Stored memories:"
        return header + "\n" + "\n".join(lines)

    if command == "identity":
        identity = state.get("identity", {})
        if not identity:
            return "No identity fields set. Use: set <key> <value>."
        lines = "\n".join(f"{k}: {v}" for k, v in identity.items() if v)
        return (
            f"Freedeon Identity:\n{lines}"
            if lines
            else "Identity fields exist but are empty. Use: set <key> <value>."
        )

    if command == "profile":
        identity = state.get("identity", {})
        name      = identity.get("name",      "").strip() or "—"
        role      = identity.get("role",      "").strip() or "—"
        mission   = identity.get("mission",   "").strip() or "—"
        territory = identity.get("territory", "").strip() or "—"
        version   = identity.get("version",   "").strip() or "—"
        return (
            f"Freedeon Profile\n"
            f"Name: {name}\n"
            f"Role: {role}\n"
            f"Mission: {mission}\n"
            f"Territory: {territory}\n"
            f"Version: {version}"
        )

    if command == "log":
        activity = state.get("activity", [])
        if not activity:
            return "Activity log is empty. No actions recorded yet."
        recent = list(reversed(activity[-10:]))
        lines = []
        for entry in recent:
            eid     = entry.get("id", "?")
            ts      = entry.get("created_at", "")[:16].replace("T", " ")
            action  = entry.get("action", "")
            inp     = entry.get("input") or ""
            ref     = entry.get("ref_id")
            ref_str = f"  → ref:{ref}" if ref is not None else ""
            lines.append(f"[{eid}] {ts}  {action:<16}{inp}{ref_str}")
        return "Activity Log\n" + "\n".join(lines)

    if command == "checkpoints":
        cps = get_checkpoints()
        if not cps:
            return "No checkpoints recorded yet. Use: checkpoint <memory_id>."
        lines = []
        for entry in cps:
            cid     = entry.get("id", "?")
            ts      = entry.get("created_at", "")[:16].replace("T", " ")
            ref     = entry.get("ref_id", "?")
            details = entry.get("details", {})
            content = details.get("content", "")
            anchor  = details.get("primary_anchor_id", "—")
            lines.append(
                f"[checkpoint:{cid}] {ts}  → mem:{ref}  "
                f"anchor:{anchor}  \"{content}\""
            )
        return "Checkpoints:\n" + "\n".join(lines)

    if command == "anchor":
        sub    = argument.strip().split(None, 1)
        subcmd = sub[0].lower() if sub else ""
        subarg = sub[1].strip() if len(sub) > 1 else ""

        # anchor list ────────────────────────────────────────────────────────
        if subcmd == "list":
            anchors = state.get("anchors", [])
            active  = [a for a in anchors
                       if isinstance(a, dict) and a.get("status") != "revoked"]
            if not active:
                return "No active anchors. Use: anchor create <label>."
            pid   = state.get("primary_anchor_id")
            lines = []
            for a in active:
                star        = "★" if a["id"] == pid else " "
                primary_tag = "  (primary)" if a["id"] == pid else ""
                lines.append(
                    f"{star} [{a['id']}] {a.get('label',''):<30} "
                    f"{a.get('chain',''):<10} {a.get('status','')}{primary_tag}"
                )
            return "Anchors:\n" + "\n".join(lines)

        # anchor resolve ─────────────────────────────────────────────────────
        if subcmd == "resolve":
            primary = get_primary_anchor()
            if primary is None:
                return "No primary anchor set. Use: anchor create <label>."
            ts = primary.get("created_at", "")[:16].replace("T", " ")
            return (
                f"Primary Anchor\n"
                f"Label:  {primary.get('label',  '—')}\n"
                f"Chain:  {primary.get('chain',  '—')}\n"
                f"Ref:    {primary.get('ref',    '—')}\n"
                f"Status: {primary.get('status', '—')}\n"
                f"Since:  {ts}"
            )

        # anchor create <label> ──────────────────────────────────────────────
        if subcmd == "create":
            if not subarg:
                return "Usage: anchor create <label>. Example: anchor create freedeon.bitmap"
            label = subarg.strip().lower()          # ── lowercase normalization
            if not label:
                return "Label cannot be empty."
            if anchor_label_exists(label):
                return (
                    f"An anchor with label '{label}' already exists. "
                    "Labels must be unique."
                )
            anchor_id = alloc_id()
            anchor = {
                "id":         anchor_id,
                "created_at": now_utc(),
                "type":       "anchor",
                "label":      label,
                "chain":      "bitmap",
                "ref":        label,
                "status":     "declared",
                "details":    {}
            }
            state["anchors"].append(anchor)
            is_first = len(state["anchors"]) == 1
            if is_first:
                state["primary_anchor_id"] = anchor_id
            record_activity(
                action     = "anchor_create",
                input_text = label,
                ref_id     = anchor_id,
                details    = {"label": label, "chain": "bitmap",
                              "set_as_primary": is_first}
            )
            save_state(state)
            primary_note = " Set as primary (first anchor)." if is_first else ""
            return (
                f"Anchor [id:{anchor_id}] created — label: \"{label}\", "
                f"chain: bitmap, status: declared.{primary_note}"
            )

        # anchor primary <id> ────────────────────────────────────────────────
        if subcmd == "primary":
            if not subarg:
                return "Usage: anchor primary <id>. Example: anchor primary 3"
            try:
                target_id = int(subarg.strip())
            except ValueError:
                return "Invalid id. Usage: anchor primary <id>."
            anchor = find_anchor_by_id(target_id)
            if anchor is None:
                return f"No anchor found with id:{target_id}."
            if anchor.get("status") == "revoked":
                return f"Anchor id:{target_id} is revoked. Cannot set as primary."
            previous_pid = state.get("primary_anchor_id")
            if previous_pid == target_id:
                return f"Anchor id:{target_id} is already the primary anchor."
            state["primary_anchor_id"] = target_id
            record_activity(
                action     = "anchor_primary",
                input_text = str(target_id),
                ref_id     = target_id,
                details    = {"previous_primary": previous_pid,
                              "new_primary":      target_id}
            )
            save_state(state)
            return (
                f"Primary anchor updated to id:{target_id} "
                f"(\"{anchor.get('label', '')}\"). "
                "The Eon's point of origin is resealed."
            )

        # anchor revoke <id> ─────────────────────────────────────────────────
        if subcmd == "revoke":
            if not subarg:
                return "Usage: anchor revoke <id>. Example: anchor revoke 3"
            try:
                target_id = int(subarg.strip())
            except ValueError:
                return "Invalid id. Usage: anchor revoke <id>."
            anchor = find_anchor_by_id(target_id)
            if anchor is None:
                return f"No anchor found with id:{target_id}."
            if anchor.get("status") == "revoked":
                return f"Anchor id:{target_id} is already revoked."
            if state.get("primary_anchor_id") == target_id:
                return (
                    "Cannot revoke the primary anchor. "
                    "Use 'anchor primary <id>' to reassign primary first."
                )
            anchor["status"]     = "revoked"
            anchor["revoked_at"] = now_utc()
            record_activity(
                action     = "anchor_revoke",
                input_text = str(target_id),
                ref_id     = target_id,
                details    = {"label": anchor.get("label", "")}
            )
            save_state(state)
            return (
                f"Anchor id:{target_id} (\"{anchor.get('label', '')}\") revoked. "
                "The entry is retained in the ledger."
            )

        return (
            "Unknown anchor subcommand. "
            "Use: anchor create | anchor list | "
            "anchor primary | anchor resolve | anchor revoke."
        )

    # ── MUTATING COMMANDS ────────────────────────────────────────────────────

    if command == "remember":
        if not argument:
            return "Nothing to remember. Provide text after 'remember'."
        mem_id = alloc_id()
        entry = {
            "id":         mem_id,
            "created_at": now_utc(),
            "type":       "memory",
            "content":    argument,
            "deleted":    False
        }
        state["memory"].append(entry)
        record_activity(
            action     = "remember",
            input_text = argument,
            ref_id     = mem_id,
            details    = {"content": argument}
        )
        save_state(state)
        return f"Remembered [id:{mem_id}]: \"{argument}\". The mesh holds it now."

    if command == "forget":
        if not argument:
            return "Usage: forget <id>. Example: forget 3"
        try:
            target_id = int(argument.strip())
        except ValueError:
            return "Invalid id. Usage: forget <id>. Id must be an integer."
        entry = find_memory_by_id(target_id)
        if entry is None:
            return f"No memory found with id:{target_id}."
        if entry.get("deleted"):
            return f"Memory id:{target_id} is already marked as deleted."
        entry["deleted"]    = True
        entry["deleted_at"] = now_utc()
        record_activity(
            action     = "forget",
            input_text = str(target_id),
            ref_id     = target_id,
            details    = {"deleted_id": target_id}
        )
        save_state(state)
        return (
            f"Memory id:{target_id} marked as deleted. "
            "The entry is retained for chain-of-custody. "
            "Use 'memory all' to view deleted entries."
        )

    if command == "checkpoint":
        if not argument:
            return "Usage: checkpoint <memory_id>. Example: checkpoint 3"
        try:
            target_id = int(argument.strip())
        except ValueError:
            return "Invalid id. Usage: checkpoint <memory_id>. Id must be an integer."
        mem_entry = find_memory_by_id(target_id)
        if mem_entry is None:
            return f"No memory found with id:{target_id}."
        if mem_entry.get("deleted"):
            return (
                f"Memory id:{target_id} is marked as deleted. "
                "Cannot checkpoint a deleted memory."
            )
        record_activity(
            action     = "checkpoint",
            input_text = str(target_id),
            ref_id     = target_id,
            entry_type = "checkpoint",
            details    = {
                "memory_id":         target_id,
                "content":           mem_entry.get("content", ""),
                "primary_anchor_id": state.get("primary_anchor_id")
            }
        )
        save_state(state)
        cp_id   = state["activity"][-1]["id"]
        primary = get_primary_anchor()
        anchor_note = (
            f" Anchor: \"{primary.get('label', '')}\"."
            if primary else ""
        )
        return (
            f"Checkpoint [id:{cp_id}] created for memory id:{target_id}. "
            f"Content: \"{mem_entry.get('content', '')}\"."
            f"{anchor_note} The moment is sealed in the ledger."
        )

    if command == "set":
        if not argument:
            return "Usage: set <key> <value>. Example: set name Charly"
        field_parts = argument.split(None, 1)
        if len(field_parts) < 2:
            return "Usage: set <key> <value>. Both a key and a value are required."
        key, value = field_parts[0].lower(), field_parts[1]
        state.setdefault("identity", {})[key] = value
        record_activity(
            action     = "set",
            input_text = argument,
            ref_id     = None,
            details    = {"field": key, "value": value}
        )
        save_state(state)
        return f"Identity field set — {key}: \"{value}\". The mesh knows you now."

    if command == "signal":
        record_activity(
            action     = "signal",
            input_text = argument if argument else None,
            ref_id     = None,
            details    = {"text": argument} if argument else None
        )
        save_state(state)
        return (
            "Signal received. "
            "Propagating through the intermesh. "
            "Your node is heard."
        )

    if command:
        return (
            f"Unknown signal: '{command}'. "
            "The mesh does not recognise this command. "
            "Try 'help' to orient yourself, sovereign."
        )

    return (
        "No command detected. "
        "Transmit a valid signal. "
        "The mesh is listening."
    )


class FreedeonHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[Freedeon] {self.address_string()} — {format % args}")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if self.path == "/signal":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                raw_command = data.get("command", "")
            except (json.JSONDecodeError, AttributeError):
                raw_command = ""
            response_text = handle_command(raw_command)
            payload = json.dumps({"response": response_text}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "endpoint not found"}')


if __name__ == "__main__":
    server  = HTTPServer(("0.0.0.0", PORT), FreedeonHandler)
    identity = state.get("identity", {})
    name     = identity.get("name", "unnamed")
    version  = identity.get("version", "v0.3")
    primary  = get_primary_anchor()
    anchor_label = primary.get("label", "none") if primary else "none"
    active_memories = sum(
        1 for e in state.get("memory", [])
        if isinstance(e, dict) and not e.get("deleted")
    )
    print(f"Freedeon node active — http://localhost:{PORT}")
    print(f"Identity: {name} | {version}")
    print(f"Memory: {active_memories} active | "
          f"Activity: {len(state.get('activity', []))} entries | "
          f"Anchors: {len(state.get('anchors', []))} | "
          f"Next ID: {state['next_id']}")
    print(f"Primary anchor: {anchor_label}")
    print("Mesh is live. Sovereignty intact.")
    server.serve_forever()