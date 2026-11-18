# Documentation

The documentation is built with Sphinx and published on Read the Docs in two languages:

- Mongolian: <https://ebarimt-pos-sdk.readthedocs.io/mn/latest/>
- English: <https://ebarimt-pos-sdk.readthedocs.io/en/latest/>

## Layout

```text
docs/
├── source/                  English sources (Markdown via MyST, reST for the API reference)
│   ├── conf.py
│   ├── index.md, installation.md, quickstart.md
│   ├── guides/              hand-written guides
│   └── api/                 API reference, generated from docstrings by autodoc
└── locale/mn/LC_MESSAGES/   Mongolian translation, one .po file per page
```

English is the source language. Mongolian is a translation of it, stored as gettext catalogues. There is only one copy of
every page, code sample and table, so the two languages cannot drift apart structurally: a paragraph without a
translation is shown in English.

The API reference (docstrings) and the changelog are English in both editions.

## Build locally

```bash
uv sync --extra docs
```

```bash
uv run --extra docs make -C docs html
```

```bash
uv run --extra docs make -C docs html-mn
```

The output is in `docs/build/html` (English) and `docs/build/html-mn` (Mongolian). CI builds both with warnings
treated as errors (`SPHINXOPTS="-W --keep-going"`).

## Changing a page

1. Edit the English page under `docs/source/`.
2. Refresh the catalogues:

   ```bash
   uv run --extra docs make -C docs update-po
   ```

3. Open the matching file in `docs/locale/mn/LC_MESSAGES/` and translate the entries that are new (empty `msgstr`)
   or marked `#, fuzzy`. Remove the `fuzzy` marker once the translation is correct; fuzzy entries are not used.
4. Build both languages and check the result.

Rules for translations:

- Keep inline markup identical: every `` `code` `` span, link target and `[](page.md)` reference in the `msgid` must
  appear in the `msgstr`.
- Do not translate identifiers, field names or code.
- Entries that consist only of code (for example a table cell with `` `client.receipt` ``) are left empty.
- Docstring entries in `api/*.po` are left empty on purpose; only the headings there are translated.

Code blocks are not part of the catalogues, so comments inside code samples stay in English.

## Read the Docs setup

Read the Docs builds one language per project and passes it to Sphinx (`-D language=<code>`), so the two languages are
two projects that build the same repository and the same `.readthedocs.yaml`:

| Project | Language setting | Role |
| --- | --- | --- |
| `ebarimt-pos-sdk` | Mongolian (`mn`) | main project |
| `ebarimt-pos-sdk-en` (any slug) | English (`en`) | added under **Translations** of the main project |

Once the English project is linked as a translation, it is served at `/en/` under the main project's domain and the
language switcher appears in the Read the Docs flyout menu. No file in this repository needs to change for that.
