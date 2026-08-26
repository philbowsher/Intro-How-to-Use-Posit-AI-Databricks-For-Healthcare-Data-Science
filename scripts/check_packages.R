# Run this before the R/reticulate workflow (new_analysis_r.qmd, Dashboard_r.qmd).
# Checks whether the R packages those documents need are installed, and
# installs any that are missing.
#
# Run it with:  Rscript scripts/check_packages.R
# (or source it from an R console: source("scripts/check_packages.R"))
#
# Tested finding: the system R library is often not writable (no sudo),
# so a plain install.packages() call can fail silently or with a permissions
# error. This script creates and uses a personal library
# (~/R/<platform>-library/<R version>, R's own default user library location)
# if the system library isn't writable -- the same problem check_packages.py
# solves for Python by using pip's own user-install fallback, made explicit
# here instead of relying on it happening implicitly.

required_packages <- c(
  "reticulate",  # bridges to the shared Python Databricks connection
  "dplyr",       # data wrangling in the R documents
  "ggplot2",     # charts in the R documents
  "gt"           # tables in Dashboard_r.qmd
)

# Pin to a DATED Posit Package Manager snapshot, not "/latest". This
# environment already points R at PPM by default (via
# /mnt/session/rstudio/repos.conf), but at /latest -- unlike the Python
# side, install.packages() has no per-call version pin, so the *snapshot
# date* is what makes this reproducible over time, not just using PPM.
# Confirmed working (2026-08-26): https://p3m.dev/cran/__linux__/jammy/2026-08-25
# resolves; the exact current date can 400 until that day's snapshot is
# finalized, so this uses yesterday's date, not today's.
options(repos = c(
  CRAN = "https://p3m.dev/cran/__linux__/jammy/2026-08-25",
  Bioc = "https://p3m.dev/bioconductor"
))

user_lib <- Sys.getenv("R_LIBS_USER")
if (nzchar(user_lib) && !dir.exists(user_lib)) {
  dir.create(user_lib, recursive = TRUE, showWarnings = FALSE)
}

# Prefer the user library if the default library isn't writable -- avoids a
# confusing permissions error partway through install.packages().
default_lib <- .libPaths()[1]
if (file.access(default_lib, mode = 2) != 0 && nzchar(user_lib)) {
  cat("[info]    Default R library (", default_lib, ") isn't writable -- using ", user_lib, "\n", sep = "")
  .libPaths(c(user_lib, .libPaths()))
}

cat("Checking", length(required_packages), "R packages...\n\n")

missing <- character(0)
for (pkg in required_packages) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    cat("[ok]     ", pkg, "\n")
  } else {
    cat("[missing]", pkg, "\n")
    missing <- c(missing, pkg)
  }
}

cat("\n")

if (length(missing) > 0) {
  cat(length(missing), "package(s) missing. Installing...\n\n")
  for (pkg in missing) {
    result <- tryCatch({
      install.packages(pkg, lib = .libPaths()[1])
      "ok"
    }, error = function(e) e, warning = function(w) w)

    if (identical(result, "ok") && requireNamespace(pkg, quietly = TRUE)) {
      cat("[installed]", pkg, "\n")
    } else {
      cat("[FAILED]   ", pkg, "\n")
      cat("           -> ", conditionMessage(if (inherits(result, "condition")) result else simpleCondition("unknown error")), "\n")
    }
  }
} else {
  cat("All R packages available.\n")
}

# Tested finding: new_analysis_r.qmd and Dashboard_r.qmd both hardcode
# use_python(file.path(getwd(), ".venv", "bin", "python"), required = TRUE).
# That's correct IF a .venv exists (see scripts/check_packages.py's .venv
# check) -- but gives no useful hint here if it's missing, since this
# script doesn't touch Python at all. Check for it explicitly so the R
# student gets pointed at the actual fix (create .venv, or run
# scripts/check_packages.py) instead of a raw reticulate error later.
cat("\n")
venv_python <- file.path(getwd(), ".venv", "bin", "python")
if (file.exists(venv_python)) {
  cat("[ok]      Found .venv at", venv_python, "-- the R documents' use_python() call will work.\n")
} else {
  cat("[warning] No .venv found at", venv_python, "\n")
  cat("           new_analysis_r.qmd and Dashboard_r.qmd hardcode this exact path via use_python().\n")
  cat("           Create it first: python3.14 -m venv .venv, then run scripts/check_packages.py\n")
  cat("           (from Python) to install the required Python packages into it.\n")
}
