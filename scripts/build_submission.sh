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

"$PY" scripts/polish_docx.py "$OUT/manuscript.docx" "$OUT/supplementary.docx"
echo "built $OUT/"
