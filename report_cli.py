"""Report each pane's detected CLI as the `cli` sidebar token: `claude · teal-lynx`.

herdr knows which runtime it detected — it keys `rows_by_agent` off it — but exposes
no built-in token for it, so the sidebar can show `teal-lynx` and never say whether a
Claude Code, a Codex or an omp is behind the name. Publishing it as pane metadata is
the only way to get it into a row.

The name half needs nothing: the built-in `agent` token already renders the pane label,
which is where agent-auto-naming persists the name. Only the runtime is missing.

A separate token rather than one combined string, because `pane report-metadata` strips
control characters — colour cannot travel in the value, it has to come from styling the
token in `[ui.sidebar.agents]`, and only a token of its own can carry a per-CLI accent.
herdr joins adjacent tokens with `·`; that separator is not configurable.

Runs on `pane.agent_detected` and `pane.agent_status_changed` for one pane, and from
the startup hook or the `refresh` action for every pane.
"""
import json, os, subprocess

HERDR = os.environ.get("HERDR_BIN_PATH", "herdr")
SOURCE = "azyu.agent-cli"


def herdr(*args):
    try:
        out = subprocess.run([HERDR, *args], capture_output=True, text=True, timeout=3)
        payload = json.loads(out.stdout or out.stderr or "{}")
    except Exception:
        return {}
    return {} if payload.get("error") else (payload.get("result") or {})


def main():
    panes = herdr("pane", "list").get("panes", [])
    event = json.loads(os.environ.get("HERDR_PLUGIN_EVENT_JSON") or "{}")
    if pane_id := (event.get("data") or {}).get("pane_id"):
        panes = [p for p in panes if p["pane_id"] == pane_id]

    for pane in panes:
        cli = pane.get("agent") or ""  # empty once the pane stops hosting an agent
        if cli == ((pane.get("tokens") or {}).get("cli") or ""):
            continue  # every write repaints the sidebar; only write on change
        flag = ["--token", f"cli={cli}"] if cli else ["--clear-token", "cli"]
        herdr("pane", "report-metadata", pane["pane_id"], "--source", SOURCE, *flag)
        print(f"{pane['pane_id']}: {cli or 'cleared'}")


if __name__ == "__main__":
    main()
