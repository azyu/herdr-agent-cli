"""Write the sidebar rows this plugin's `cli` token needs into herdr's config.toml.

The plugin reports a value; where it lands and what colour it takes is sidebar
configuration, and herdr gives a plugin no way to supply that — config.toml has no
include and the manifest has no ui fields. Most plugins that report a token ask the
user to paste one line. Ours is twenty-two, with a rule cap and a row that has to be
kept in step, so it writes them: between markers, with a backup, putting the file back
if herdr rejects the result.

Defaults are PALETTE below. Overrides go in the plugin's own config dir, which survives
plugin updates and is where herdr's docs say user-editable config belongs:

    $(herdr plugin config-dir azyu.agent-cli)/config.toml

        colours = "off"        # never touch herdr's config

        [colors]
        claude = "#ff8800"     # any canonical agent id herdr knows

Runs from the `[[startup]]` hook — not `[[build]]`, which gets no runtime environment
and which `herdr plugin link` skips entirely — and from the `configure` action. A run
with nothing to change writes nothing and reloads nothing. `--remove` backs it out.
"""
import json, os, pathlib, shutil, subprocess, sys

HERDR = os.environ.get("HERDR_BIN_PATH", "herdr")
CONFIG = pathlib.Path(os.environ.get("HERDR_CONFIG_PATH")
                      or pathlib.Path.home()/".config/herdr/config.toml")
PLUGIN_CONFIG = pathlib.Path(os.environ.get("HERDR_PLUGIN_CONFIG_DIR") or ".")/"config.toml"
START, END = "# >>> azyu.agent-cli >>>", "# <<< azyu.agent-cli <<<"

ROW1 = '["state_icon", "machine", "workspace", "tab"]'
MAX_RULES = 16  # herdr's cap: "sidebar tokens may contain at most 16 rules"

# Every canonical agent id herdr 0.9.0 accepts; an unknown one is rejected outright.
# Brand colour where the CLI has one, catppuccin otherwise. The first MAX_RULES become
# inline rules on the shared row; the rest need a rows_by_agent entry each, so keep the
# ones people actually run at the top.
PALETTE = [
    ("claude", "#d97757"), ("codex", "#89dceb"), ("omp", "#f5c2e7"), ("agy", "#e8a0b8"),
    ("gemini", "#89b4fa"), ("cursor", "#94e2d5"), ("copilot", "#b4befe"),
    ("opencode", "#a6e3a1"), ("pi", "#f9e2af"), ("amp", "#fab387"), ("droid", "#f38ba8"),
    ("grok", "#bac2de"), ("kimi", "#cba6f7"), ("qwen", "#b5e8b0"), ("cline", "#eba0ac"),
    ("devin", "#74c7ec"),
    # Past the cap — one rows_by_agent line each.
    ("hermes", "#a0d8e8"), ("kilo", "#f5e0dc"), ("kiro", "#f2cdcd"), ("maki", "#e8c5a0"),
    ("muse", "#d3a6f7"), ("qodercli", "#a6adc8"),
]


def palette():
    """PALETTE with the user's plugin-config-dir overrides applied, or None if opted out."""
    if not PLUGIN_CONFIG.exists():
        return PALETTE
    import tomllib
    prefs = tomllib.loads(PLUGIN_CONFIG.read_text())
    if prefs.get("colours") == "off":
        return None
    overrides = prefs.get("colors") or {}
    if unknown := set(overrides) - {k for k, _ in PALETTE}:
        sys.exit(f"{PLUGIN_CONFIG}: not canonical agent ids: {', '.join(sorted(unknown))}")
    return [(k, overrides.get(k, c)) for k, c in PALETTE]


def block(colours):
    # Wrapped three to a line: this ends up in a file people read and diff.
    rules = [f'{{ equals = "{k}", fg = "{c}" }}' for k, c in colours[:MAX_RULES]]
    lines = [", ".join(rules[i:i + 3]) + "," for i in range(0, len(rules), 3)]
    lines[-1] = lines[-1].rstrip(",")
    cli = '{ token = "$cli", bold = true, rules = [\n    ' + "\n    ".join(lines) + "] }"
    overflow = colours[MAX_RULES:]
    w = max((len(k) for k, _ in overflow), default=0)
    extra = "\n".join(
        f'{k:<{w}} = [{ROW1}, [{{ token = "$cli", fg = "{c}", bold = true }}, "agent"]]'
        for k, c in overflow)
    return f"""{START}
# azyu.agent-cli reports the detected runtime as the $cli token; `agent` is herdr's
# own token for the pane label. Adjacent tokens are joined with `·`.
# Generated — override per runtime in
# $(herdr plugin config-dir azyu.agent-cli)/config.toml
[ui.sidebar.agents]
rows = [{ROW1}, [{cli}, "agent"]]

# A token takes at most {MAX_RULES} rules, so the rest get a row layout of their own.
# Each one replaces the whole layout for that runtime, hence row 1 repeated verbatim.
[ui.sidebar.agents.rows_by_agent]
{extra}
{END}"""


def reload():
    try:
        out = subprocess.run([HERDR, "server", "reload-config"],
                             capture_output=True, text=True, timeout=5)
        return json.loads(out.stdout)["result"].get("diagnostics") or []
    except Exception:
        return []  # no server yet (startup hook) — config is on disk for the next start


def write(text, what):
    backup = CONFIG.with_suffix(CONFIG.suffix + ".agent-cli-bak")
    if CONFIG.exists():
        shutil.copy(CONFIG, backup)  # copy, not move: config.toml is often a symlink
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(text)
    if diagnostics := reload():
        if backup.exists():
            shutil.copy(backup, CONFIG)
            reload()
        sys.exit("herdr rejected the config, restored the original:\n  "
                 + "\n  ".join(diagnostics))
    backup.unlink(missing_ok=True)
    # config.toml is often a symlink; name the file that actually changed.
    print(f"{what} {os.path.realpath(CONFIG)}")


def apply():
    colours = palette()
    if colours is None:
        return  # colours = "off": touch nothing, say nothing
    text = CONFIG.read_text() if CONFIG.exists() else ""
    want = block(colours)
    if START in text and END in text:
        head, rest = text.split(START, 1)
        tail = rest.split(END, 1)[1]
        if head + want + tail == text:
            return  # nothing to change: no write, no reload, no log
        write(head + want + tail, "updated")
    elif "[ui.sidebar.agents]" in text:
        sys.exit(f"{CONFIG} already defines [ui.sidebar.agents] and TOML will not let a\n"
                 "second one be added. Delete that block and re-run, or paste the `rows`\n"
                 "and `rows_by_agent` keys from the README into it by hand.")
    else:
        write(text.rstrip() + "\n\n" + want + "\n", "added sidebar rows to")


def remove():
    text = CONFIG.read_text() if CONFIG.exists() else ""
    if START not in text or END not in text:
        return print("nothing to remove")
    head, rest = text.split(START, 1)
    write(head.rstrip() + "\n" + rest.split(END, 1)[1].lstrip("\n"),
          "removed sidebar rows from")


if __name__ == "__main__":
    remove() if "--remove" in sys.argv else apply()
