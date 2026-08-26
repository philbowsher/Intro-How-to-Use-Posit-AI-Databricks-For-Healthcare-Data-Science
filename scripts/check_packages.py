"""Run this FIRST, before anything else in the workshop.

Checks whether the packages used later are installed, and installs any that
are missing, one at a time so a failure is diagnosed individually instead of
disappearing into a wall of pip output. Takes a few seconds if everything's
already there.

Run it with:  python scripts/check_packages.py
(from your project root, with your .venv's Python active)

Environment this was built/tested against (to replicate in a new session):
  Python 3.14.2, pip installing from PyPI (no dated snapshot needed here --
  see note below on why that's a genuine difference from an R/CRAN workflow).

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

Why no dated-snapshot pin (unlike the R/check_packages.R this is modeled on):
pip/PyPI doesn't have an MRAN/Posit-Package-Manager-style dated mirror to
pin against -- every published version stays available forever at its own
exact version string. Pinning exact versions (below) is the closest
equivalent: it's reproducible without needing a special index URL.
"""

import importlib
import subprocess
import sys

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
            [sys.executable, "-m", "pip", "install", pin],
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


def check_quarto() -> None:
    result = subprocess.run(["which", "quarto"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[ok]      Quarto found on PATH: {result.stdout.strip()}")
    else:
        print(
            "[warning] Quarto not found on PATH. You'll need it to render the .qmd workflows. "
            "See https://quarto.org/docs/get-started/"
        )
    import os

    if not os.environ.get("QUARTO_PYTHON"):
        print(
            "[info]    QUARTO_PYTHON is not set in this shell. Quarto needs this to find the right "
            "Python for rendering .qmd files -- set it in your .env as "
            "QUARTO_PYTHON=.venv/bin/python (see .env.example)."
        )


if __name__ == "__main__":
    check_python_version()
    check_and_install()
    print()
    check_quarto()
