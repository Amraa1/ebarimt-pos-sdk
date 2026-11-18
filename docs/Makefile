# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXINTL    ?= sphinx-intl
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help html-mn update-po Makefile

# Mongolian build -> build/html-mn (plain "make html" builds English).
html-mn:
	@$(SPHINXBUILD) -b html -D language=mn "$(SOURCEDIR)" "$(BUILDDIR)/html-mn" $(SPHINXOPTS) $(O)

# Re-extract translatable strings and merge them into locale/mn/*.po.
# Run after editing any page, then fill in the new/fuzzy msgstr entries.
update-po:
	@$(SPHINXBUILD) -b gettext "$(SOURCEDIR)" "$(BUILDDIR)/gettext" $(SPHINXOPTS) $(O)
	@# The changelog is kept in English only; do not create a catalogue for it.
	@rm -f "$(BUILDDIR)/gettext/changelog.pot"
	@$(SPHINXINTL) update -p "$(BUILDDIR)/gettext" -d locale -l mn

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
