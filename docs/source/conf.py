# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version

# -- Project information -----------------------------------------------------

project = "ebarimt-pos-sdk"
copyright = "2026, Amraa1"
author = "Amraa1"

try:
    release = _dist_version("ebarimt-pos-sdk")
except PackageNotFoundError:  # docs built without installing the package
    release = "unknown"
version = release

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

exclude_patterns = ["_build"]

# -- Internationalisation ----------------------------------------------------
# The sources are written in English. Mongolian lives in
# ``docs/locale/mn/LC_MESSAGES/*.po`` (see docs/README.md).
#
# Read the Docs builds each language as its own project and passes
# ``-D language=<code>``, which overrides the default below. Locally use
# ``make html`` (English) or ``make html-mn`` (Mongolian).

language = "en"
locale_dirs = ["../locale"]
gettext_compact = False
# Keep the .po files free of line numbers and UUIDs so that editing a page does
# not produce a diff in every catalogue entry below the edit.
gettext_location = False
gettext_uuid = False

# -- MyST --------------------------------------------------------------------

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

# -- autodoc -----------------------------------------------------------------

autodoc_member_order = "bysource"
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    # pydantic internals that add noise to every model
    "exclude-members": "model_config, model_fields, model_computed_fields",
}

# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_title = f"{project} {release}"
html_static_path = ["_static"]
html_css_files = ["custom.css"]


def _hide_model_signature(app, what, name, obj, options, signature, return_annotation):
    """Drop the constructor signature of pydantic models.

    It repeats every field under its camelCase alias, directly above the
    field list that already documents them under the Python name.
    """
    from pydantic import BaseModel

    if what == "class" and isinstance(obj, type) and issubclass(obj, BaseModel):
        return ("", None)
    return None


def setup(app):
    app.connect("autodoc-process-signature", _hide_model_signature)
