# Configuration file for the Sphinx documentation builder.

import sys
from pathlib import Path

# Add src to path for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

project = "lightodm"
copyright = "2026, Andrey Vykhodtsev (Aprova GmbH)"
author = "Andrey Vykhodtsev"
release = "0.2.0"
version = "0.2.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}
