#!/usr/bin/env bash
# build_submission.sh
# -------------------
# Rebuild the Journal of Neuroscience Methods package in submission_jnm/
# from the markdown sources.
#
# Smart punctuation is switched off (-smart) because it turns every "--wls"
# written outside a code span into an en dash. Styles, margins and the
# page-number footer come from the reference documents in templates/.
# polish_docx.py refuses to run while a file is open in Word.
#
# Usage:
#     bash scripts/build_submission.sh

set -euo pipefail
cd "$(dirname "$0")/.."

OUT=submission_jnm
PY=${PYTHON:-.venv_paper/bin/python}

pandoc article_jnm.md -f markdown-smart -o "$OUT/manuscript.docx" \
    --reference-doc=templates/reference_manuscript.docx
pandoc supplementary_jnm.md -f markdown-smart -o "$OUT/supplementary.docx" \
    --reference-doc=templates/reference_manuscript.docx --resource-path=.
pandoc highlights_jnm.md -f markdown-smart -o "$OUT/highlights.docx" \
    --reference-doc=templates/reference_highlights.docx
pandoc cover_letter_jnm.md -f markdown-smart -o "$OUT/cover_letter.docx" \
    --reference-doc=templates/reference_highlights.docx
pandoc response_to_reviewers_jnm.md -f markdown-smart -o "$OUT/response_to_reviewers.docx" \
    --reference-doc=templates/reference_highlights.docx

"$PY" scripts/polish_docx.py "$OUT/manuscript.docx" "$OUT/supplementary.docx"
"$PY" - "$OUT" <<'EOF'
# Strip pandoc's heading bookmarks from the short documents too; Word draws
# them as grey square brackets when "Show bookmarks" is enabled.
import sys, zipfile, shutil
from pathlib import Path
sys.path.insert(0, "scripts")
from polish_docx import strip_bookmarks
for name in ("cover_letter", "response_to_reviewers", "highlights"):
    p = Path(sys.argv[1]) / f"{name}.docx"; tmp = p.with_suffix(".tmp.docx")
    with zipfile.ZipFile(p) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            d = zin.read(it.filename)
            if it.filename == "word/document.xml":
                d = strip_bookmarks(d.decode())[0].encode()
            zout.writestr(it, d)
    shutil.move(tmp, p)
EOF
echo "built $OUT/"
