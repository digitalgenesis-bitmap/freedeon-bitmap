from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone
import json
import os

PORT = 8000
STATE_FILE = "state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}
    else:
        data = {}

    data.setdefault("memory", [])
    data.setdefault("identity", {"version": "v0.3"})
    data.setdefault("knowledge", {})
    data.setdefault("activity", [])

    if "next_id" not in data:
        highest = 0
        for entry in data["memory"]:
            if isinstance(entry, dict):
                highest = max(highest, entry.get("id", 0))
        for entry in data["activity"]:
            if isinstance(entry, dict):
                highest = max(highest, entry.get("id", 0))
        data["next_id"] = highest + 1

    return data


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


state = load_state()


def alloc_id():
    nid = state["next_id"]
    state["next_id"] = nid + 1
    return nid


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_activity(action, input_text=None, ref_id=None, details=None, entry_type=None):
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

def get_checkpoints():
    return [
        e for e in state.get("activity", [])
        if isinstance(e, dict) and e.get("type") == "checkpoint"
    ]

def handle_command(raw_command):
    parts = raw_command.strip().split(None, 1)
    command = parts[0].lower() if parts else ""
    argument = parts[1] if len(parts) > 1 else ""

    # ── READ-ONLY COMMANDS (no activity generated) ───────────────────────────

    if command == "help":
        return (
            "Commands: help | status | memory | memory all | territory | signal | "
            "remember <text> | forget <id> | checkpoint <id> | checkpoints | "
            "set <key> <value> | "
            "identity | profile | log. "
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
                eid     = entry.get("id", "?")
                ts      = entry.get("created_at", "")[:16].replace("T", " ")
                text    = entry.get("content", "")
                marker  = " [deleted]" if entry.get("deleted") else ""
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
            lines.append(f"[{eid}] {ts}  {action:<12}{inp}{ref_str}")
        return "Activity Log\n" + "\n".join(lines)
    
    if command == "checkpoints":
        cps = get_checkpoints()

        if not cps:
            return "No checkpoints recorded yet. Use: checkpoint <memory_id>."

        lines = []

        for entry in cps:
            cid = entry.get("id", "?")
            ts = entry.get("created_at", "")[:16].replace("T", " ")
            ref = entry.get("ref_id", "?")

            content = ""
            details = entry.get("details")

            if details:
                content = details.get("content", "")

            lines.append(
                f"[checkpoint:{cid}] {ts} → mem:{ref} \"{content}\""
            )

        return "Checkpoints:\n" + "\n".join(lines)
    

    # ── MUTATING COMMANDS (activity generated after each) ────────────────────

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
            action="checkpoint",
            input_text=str(target_id),
            ref_id=target_id,
            entry_type="checkpoint",
            details={
                "memory_id": target_id,
                "content": mem_entry.get("content", "")
            }
        )

        save_state(state)

        cp_id = state["activity"][-1]["id"]

        return (
            f"Checkpoint [id:{cp_id}] created for memory id:{target_id}. "
            f"Content: \"{mem_entry.get('content', '')}\". "
            "The moment is sealed in the ledger."
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
    server = HTTPServer(("0.0.0.0", PORT), FreedeonHandler)
    identity = state.get("identity", {})
    name    = identity.get("name", "unnamed")
    version = identity.get("version", "v0.3")
    active_memories = sum(
        1 for e in state.get("memory", [])
        if isinstance(e, dict) and not e.get("deleted")
    )
    print(f"Freedeon node active — http://localhost:{PORT}")
    print(f"Identity: {name} | {version}")
    print(f"Memory: {active_memories} active | "
          f"Activity: {len(state.get('activity', []))} entries | "
          f"Next ID: {state['next_id']}")
    print("Mesh is live. Sovereignty intact.")
    server.serve_forever()
