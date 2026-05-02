#!/usr/bin/env python3
"""
AI Employee Vault — Dashboard API Server
Serves real-time data from the vault's folders and log files.
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import yaml
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# ── Vault root (go up one level from dashboard/) ──────────────────────────────
VAULT_DIR = Path(__file__).parent.parent.resolve()

FOLDERS = {
    "needs_action":     VAULT_DIR / "Needs_Action",
    "pending_approval": VAULT_DIR / "Pending_Approval",
    "approved":         VAULT_DIR / "Approved",
    "plans":            VAULT_DIR / "Plans",
    "done":             VAULT_DIR / "Done",
    "failed":           VAULT_DIR / "Failed",
    "rejected":         VAULT_DIR / "Rejected",
    "logs":             VAULT_DIR / "Logs",
    "inbox":            VAULT_DIR / "Inbox",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a markdown file."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
            except yaml.YAMLError:
                fm = {}
            body = text[end + 3:].strip()
            return fm, body
    return {}, text.strip()


def read_md_file(path: Path) -> dict:
    """Read a markdown file and return a dict of its metadata + content."""
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception:
        raw = ""

    fm, body = parse_frontmatter(raw)

    # Infer type from filename if frontmatter doesn't have it
    ftype = fm.get("type", "")
    if not ftype:
        if "linkedin" in path.name.lower():
            ftype = "linkedin_post"
        elif path.name.upper().startswith("PLAN_"):
            ftype = "plan"
        else:
            ftype = "email"

    # Parse dates nicely
    created_raw = fm.get("created") or fm.get("received") or ""
    try:
        created_dt = datetime.fromisoformat(str(created_raw))
        created_iso = created_dt.isoformat()
    except Exception:
        stat_time = path.stat().st_mtime
        created_iso = datetime.fromtimestamp(stat_time).isoformat()

    # Build a clean display title
    subject = fm.get("subject") or fm.get("title") or ""
    if not subject:
        # Derive from filename
        name = path.stem
        name = re.sub(r"^(PLAN_|email_|linkedin_post_)\d+_\d+_", "", name)
        subject = name.replace("_", " ").replace("--", "—")

    return {
        "id": path.name,
        "name": path.name,
        "path": str(path),
        "type": ftype,
        "subject": subject,
        "from_": fm.get("from", ""),
        "to": fm.get("to", ""),
        "priority": fm.get("priority", "medium"),
        "status": fm.get("status", ""),
        "action_type": fm.get("action_type", ftype),
        "created": created_iso,
        "frontmatter": fm,
        "body": body,
        "size": path.stat().st_size,
    }


def list_folder(folder_key: str) -> list[dict]:
    folder = FOLDERS.get(folder_key)
    if not folder or not folder.exists():
        return []
    files = []
    for f in sorted(folder.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.name.startswith("."):
            continue
        files.append(read_md_file(f))
    return files


def load_all_logs() -> list[dict]:
    logs_dir = FOLDERS["logs"]
    entries = []
    if not logs_dir.exists():
        return entries
    for f in sorted(logs_dir.glob("*.json"), reverse=True)[:7]:  # last 7 days
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                entries.extend(data)
        except Exception:
            pass
    # Sort newest first
    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return entries[:200]


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/stats")
def api_stats():
    stats = {
        "needs_action":     len(list(FOLDERS["needs_action"].glob("*.md"))) if FOLDERS["needs_action"].exists() else 0,
        "pending_approval": len(list(FOLDERS["pending_approval"].glob("*.md"))) if FOLDERS["pending_approval"].exists() else 0,
        "approved":         len(list(FOLDERS["approved"].glob("*.md"))) if FOLDERS["approved"].exists() else 0,
        "done":             len(list(FOLDERS["done"].glob("*.md"))) if FOLDERS["done"].exists() else 0,
        "failed":           len(list(FOLDERS["failed"].glob("*.md"))) if FOLDERS["failed"].exists() else 0,
        "rejected":         len(list(FOLDERS["rejected"].glob("*.md"))) if FOLDERS["rejected"].exists() else 0,
        "plans":            len(list(FOLDERS["plans"].glob("*.md"))) if FOLDERS["plans"].exists() else 0,
    }

    # Activity from logs
    logs = load_all_logs()
    action_counts: dict[str, int] = {}
    for entry in logs:
        action = entry.get("action", "unknown")
        action_counts[action] = action_counts.get(action, 0) + 1

    stats["total_actions"] = len(logs)
    stats["action_breakdown"] = action_counts
    stats["recent_activity"] = logs[:10]
    return jsonify(stats)


@app.route("/api/folder/<folder_key>")
def api_folder(folder_key: str):
    if folder_key not in FOLDERS:
        return jsonify({"error": "Unknown folder"}), 404
    return jsonify(list_folder(folder_key))


@app.route("/api/file/<folder_key>/<filename>")
def api_file(folder_key: str, filename: str):
    if folder_key not in FOLDERS:
        return jsonify({"error": "Unknown folder"}), 404
    path = FOLDERS[folder_key] / filename
    if not path.exists():
        return jsonify({"error": "File not found"}), 404
    return jsonify(read_md_file(path))


@app.route("/api/approve/<filename>", methods=["POST"])
def api_approve(filename: str):
    """Move a file from Pending_Approval → Approved."""
    src = FOLDERS["pending_approval"] / filename
    if not src.exists():
        return jsonify({"error": "File not found in Pending_Approval"}), 404
    dest = FOLDERS["approved"] / filename
    try:
        shutil.move(str(src), str(dest))
        return jsonify({"success": True, "message": f"'{filename}' moved to Approved/"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reject/<filename>", methods=["POST"])
def api_reject(filename: str):
    """Move a file from Pending_Approval → Rejected."""
    src = FOLDERS["pending_approval"] / filename
    if not src.exists():
        return jsonify({"error": "File not found in Pending_Approval"}), 404
    dest = FOLDERS["rejected"] / filename
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        return jsonify({"success": True, "message": f"'{filename}' moved to Rejected/"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/logs")
def api_logs():
    return jsonify(load_all_logs())


@app.route("/api/agent-log")
def api_agent_log():
    log_file = FOLDERS["logs"] / "agent.log"
    if not log_file.exists():
        return jsonify({"lines": []})
    try:
        lines = log_file.read_text(encoding="utf-8").splitlines()
        return jsonify({"lines": lines[-200:]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/all-items")
def api_all_items():
    """Return every item across all workflow folders for the timeline view."""
    result = []
    for key in ["needs_action", "pending_approval", "approved", "done", "failed", "rejected", "plans"]:
        for item in list_folder(key):
            item["folder"] = key
            result.append(item)
    result.sort(key=lambda x: x.get("created", ""), reverse=True)
    return jsonify(result)


if __name__ == "__main__":
    print("🚀 AI Employee Dashboard running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000, host="127.0.0.1")
