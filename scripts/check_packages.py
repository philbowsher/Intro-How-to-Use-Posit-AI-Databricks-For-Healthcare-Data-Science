"""Run this FIRST, before anything else in the workshop.

Checks whether the packages used later are installed, and installs any that
are missing, one at a time so a failure is diagnosed individually instead of
disappearing into a wall of pip output. Takes a few seconds if everything's
already there.

Run it with:  python scripts/check_packages.py
(from your project root, with your .venv's Python active)

Environment this was built/tested against (to replicate in a new session):
  Python 3.14.2, pip installing from Posit Package Manager's Python mirror
  (see PPM_PYPI_INDEX below), not directly from PyPI.

Tested finding (2026-08-26): every package below has a prebuilt wheel for
Python 3.14 on manylinux (cp314 wheels exist for pyarrow, pydantic-core,
rpds-py, watchfiles, etc. -- the C-extension packages that would be most at
risk on a very new Python). A full `pip install` of this exact list into a
clean 3.14.2 venv completed with zero compile steps and zero failures. So,
unlike the R/CRAN workshop this pattern is adapted from (which hit a real
source-compile failure), there is currently no known package-install gotcha
for this stack on Python 3.14.2. Don't assume that holds forever -- PyPI
wheels for a new CPython version can lag right after release -- but as of
this test, it's a non-issue. If you hit an install failure that this script
doesn't already explain, that's new information: add it to
.posit/assistant/skills/databricks-healthcare-workshop/SKILL.md so the next
session doesn't rediscover it from scratch.

Uses Posit Package Manager's Python mirror (this environment already has
one configured for R via /mnt/session/rstudio/repos.conf -- confirmed by
checking, not assumed) rather than public PyPI directly. Unlike the R
script, this doesn't need a *dated* snapshot: every package below is
already pinned to an exact version with `==`, so pointing at PPM's
`/latest` Python index is still fully reproducible -- the exact version
string is what's pinned, not "whatever's newest." Tested: the full package
list below installs and imports cleanly from this index on Python 3.14.2.
"""

PPM_PYPI_INDEX = "https://p3m.dev/pypi/latest/simple"

import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path

# Exact versions confirmed to install together cleanly on Python 3.14.2
# (see tested finding above). Pin format is "distribution==version"; the
# dict value is the importable module name where it differs from the
# distribution name.
REQUIRED_PACKAGES = {
    "databricks-sql-connector==4.4.0": "databricks.sql",
    "polars==1.44.0": "polars",
    "plotly==7.0.0": "plotly",
    "shiny==1.7.0": "shiny",
    "streamlit==1.62.0": "streamlit",
    "python-dotenv==1.2.3": "dotenv",
    "nbformat==5.11.1": "nbformat",
    "nbclient==0.11.0": "nbclient",
    "nbconvert==7.17.1": "nbconvert",
    "ipykernel==7.3.0": "ipykernel",
    "pandera==0.32.1": "pandera",
    # Tested finding: needed for interactive Plotly charts inside Shiny for
    # Python (app.py's Workflow 3 prompts) via shinywidgets.render_plotly /
    # render_widget. Missing from an earlier version of this list -- a
    # student following the scripted prompts hit ModuleNotFoundError with
    # nothing catching it first.
    "shinywidgets==0.8.1": "shinywidgets",
    # Tested finding (2026-08-26): Quarto's Jupyter engine imports pyyaml
    # internally (share/jupyter/jupyter.py -> notebook.py) to parse notebook
    # metadata. It's not a package this workshop's code imports directly,
    # but `quarto render` on any .qmd with a Python code cell fails with
    # "ModuleNotFoundError: No module named 'yaml'" without it. Not obvious
    # from any of this workshop's own import statements -- add it here so
    # check_packages.py catches it before a student hits it mid-render.
    "pyyaml==6.0.3": "yaml",
}

REQUIRED_PYTHON = (3, 14)

# Tested finding: `shiny` and `streamlit` install a CLI command as part of
# their package -- but on a non-writable Python (no .venv, no sudo), pip
# silently falls back to a --user install, and that command's script often
# lands in ~/.local/bin, which isn't on PATH. check_and_install() reporting
# "installed" doesn't mean `streamlit run ...` (the exact command the
# workshop tells you to type) will actually be found by your shell.
CLI_COMMANDS = {"shiny": "shiny", "streamlit": "streamlit"}


def check_venv() -> None:
    """Tested finding: nothing in this workshop forces a .venv to exist, but
    three separate things silently assume one does: QUARTO_PYTHON=.venv/bin/python
    in .env, and the hardcoded use_python(getwd()/.venv/bin/python) call in
    both new_analysis_r.qmd and Dashboard_r.qmd. A student who opens this
    folder directly (rather than using Positron's File > New Project > Python,
    which creates .venv automatically) will hit confusing failures in three
    unrelated places later, with no single clear error pointing back here.
    """
    venv_python = Path(".venv") / "bin" / "python"
    in_venv = sys.prefix != sys.base_prefix

    if not venv_python.exists():
        print(
            "[warning] No .venv found at .venv/bin/python. This project's .env "
            "(QUARTO_PYTHON=.venv/bin/python) and both R/reticulate documents "
            "(new_analysis_r.qmd, Dashboard_r.qmd) hardcode this path and will fail "
            "without it. Create one now, then re-run this script from inside it:\n"
            "             python3.14 -m venv .venv\n"
            "             .venv/bin/python scripts/check_packages.py\n"
            "           Or use Positron's File > New Project > Python, which creates "
            "and selects .venv for you automatically.\n"
        )
    elif not in_venv:
        print(
            "[info]    .venv exists, but this script isn't currently running inside it. "
            "Set Positron's Python interpreter (top-right corner) to .venv before continuing.\n"
        )
    else:
        print("[ok]      Running inside .venv.\n")


def check_cli_commands() -> None:
    """Tested finding: checking shutil.which(command) against the *system*
    PATH is unreliable here -- a stale, unrelated install elsewhere on PATH
    can make this report a false "ok" for a command that has nothing to do
    with this project's .venv. What actually matters is whether the script
    written into THIS .venv (.venv/bin/<command>) is reachable, which means
    checking whether .venv/bin itself is on PATH, not just whether *some*
    command by that name resolves anywhere on the system.
    """
    import os

    venv_bin = Path(".venv") / "bin"
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    venv_bin_on_path = str(venv_bin.resolve()) in [
        str(Path(p).resolve()) for p in path_dirs if p
    ]

    for module_name, command in CLI_COMMANDS.items():
        if importlib.util.find_spec(module_name) is None:
            continue  # not installed at all -- already reported above
        venv_script = venv_bin / command
        if not venv_script.exists():
            continue  # installed but not via this .venv -- nothing to check here
        if venv_bin_on_path:
            print(f"[ok]      `{command}` found in .venv/bin, and .venv/bin is on PATH")
        else:
            print(
                f"[warning] `{command}` exists at .venv/bin/{command}, but .venv/bin isn't on "
                f"PATH in this shell -- a bare `{command} run ...` (what the workshop tells you "
                f"to run) may resolve to a different, unrelated install elsewhere on PATH, or "
                f"fail entirely. Activate the venv first (e.g. `source .venv/bin/activate`), or "
                f"run `.venv/bin/{command} run ...` / `.venv/bin/python -m {command} run ...` "
                f"explicitly."
            )


def check_python_version() -> None:
    """Real gotcha (tested): a plain `python3 -m venv .venv` on this system
    resolves to whichever Python happens to be first on PATH -- which was a
    system Python 3.12.3 during testing, NOT the 3.14.2 this project pins in
    pyproject.toml. Positron's "New Project > Python" flow picks the right
    interpreter for you, but running `python3 -m venv` by hand from a
    terminal will silently give you the wrong Python version with no error.
    Check this explicitly rather than letting it surface later as a
    confusing package-version mismatch.
    """
    current = sys.version_info[:2]
    print(f"Python interpreter: {sys.executable} (version {sys.version.split()[0]})")
    print("(Make sure this matches the interpreter Positron's console, Quarto, and your terminal all use.)")
    if current < REQUIRED_PYTHON:
        print(
            f"[warning] This project expects Python >= {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}, "
            f"but this interpreter is {current[0]}.{current[1]}.\n"
            "           If you created your venv with a bare `python3 -m venv .venv`, that command "
            "uses whatever `python3` resolves to on PATH, which may not be the version this project "
            "pins. In Positron, use File > New Project > Python and let it manage the interpreter, "
            "or explicitly point venv creation at the right interpreter, e.g.:\n"
            "           /path/to/python3.14 -m venv .venv\n"
        )
    else:
        print("[ok]      Python version matches project requirement.\n")


def check_and_install() -> None:
    print(f"Checking {len(REQUIRED_PACKAGES)} packages...\n")

    missing = []
    for pin, module_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module_name)
            print(f"[ok]      {pin}")
        except ImportError:
            print(f"[missing] {pin}")
            missing.append(pin)

    print()

    if not missing:
        print("All packages available. You're ready for the workshop.")
        return

    print(
        f"{len(missing)} package(s) missing. Installing one at a time so failures "
        "are diagnosed individually instead of as one wall of pip output...\n"
    )

    failed = []
    for pin in missing:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--index-url", PPM_PYPI_INDEX, pin],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"[installed] {pin}")
        else:
            failed.append(pin)
            print(f"[FAILED]    {pin}")
            tail = "\n".join(result.stderr.strip().splitlines()[-5:])
            print(f"            -> pip's last few lines of output:\n{tail}")
            print(
                "            -> If this is a 'no matching distribution' or wheel-build error, it's "
                "likely a Python-version mismatch (see the Python version check above) rather than "
                "a real incompatibility -- confirm you're on the interpreter this project expects."
            )

    print()
    if failed:
        print("Still missing:", ", ".join(failed), "-- see hints above.")
    else:
        print("All packages now installed.")
        print(
            "If you already had a Python console/kernel open before running this, restart it "
            "now -- a running session doesn't always see packages installed after it started."
        )


def check_quarto() -> None:
    result = subprocess.run(["which", "quarto"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[ok]      Quarto found on PATH: {result.stdout.strip()}")
    else:
        print(
            "[warning] Quarto not found on PATH. You'll need it to render the .qmd workflows. "
            "See https://quarto.org/docs/get-started/"
        )

    # Tested finding: .env's QUARTO_PYTHON only affects `quarto render` run from
    # the CLI with that env var exported. Positron's own Render button ignores
    # it and uses whatever interpreter is selected top-right instead. Checking
    # this interpreter (the one running this script) against .env's declared
    # value at least catches the common case: running check_packages.py from
    # the same interpreter you intend to use for everything else.
    try:
        from dotenv import dotenv_values

        env_values = dotenv_values(".env")
    except Exception:
        env_values = {}

    quarto_python = env_values.get("QUARTO_PYTHON")
    if not quarto_python:
        print(
            "[info]    QUARTO_PYTHON not found in .env. Quarto needs this to find the right "
            "Python for CLI renders -- set it to QUARTO_PYTHON=.venv/bin/python (see .env.example). "
            "Note this does NOT control Positron's Render button (see next check)."
        )
    else:
        declared = Path(quarto_python).resolve()
        current = Path(sys.executable).resolve()
        if declared == current:
            print(f"[ok]      This interpreter matches .env's QUARTO_PYTHON ({declared}).")
        else:
            print(
                f"[warning] This interpreter ({current}) does not match .env's QUARTO_PYTHON "
                f"({declared}). That's fine for this check itself, but remember: neither one "
                f"controls Positron's Render button -- that uses whatever interpreter is "
                f"selected top-right in Positron. Set that selector to .venv explicitly; don't "
                f"assume .env covers it."
            )


if __name__ == "__main__":
    check_python_version()
    check_venv()
    check_and_install()
    print()
    check_cli_commands()
    print()
    check_quarto()
