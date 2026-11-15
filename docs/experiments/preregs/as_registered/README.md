# as_registered/ — the exact text a stored result pins

Every file here is a byte-exact copy of a pre-registration as it stood when a stored result recorded
its SHA-256. The name is `<first 12 hex of the file's own SHA-256>__<original file name>`, so
`sha256sum` of any file reproduces its prefix. `tools/registration_ledger.py` extracts them from git
history, and so do the seven taken from `postreview_completion.json` on 2026-11-14. Together they make
all 23 pinned hashes obtainable from the tree, without history.

**Do not edit these files, and do not fix the links inside them.** The relative links were written
for each file's original location (`docs/experiments/preregs/` or the older `specs/experiments/`), so
many no longer resolve from here. Editing a file would change its hash, and then it would no longer
be the text the result pins. To find the live document, look the file's ID up in
[`../../REGISTRY.md`](../../REGISTRY.md).
