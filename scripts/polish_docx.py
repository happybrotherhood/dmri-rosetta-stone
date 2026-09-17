"""
polish_docx.py
--------------
Clean up the two cosmetic artefacts pandoc leaves in a .docx:

1. Bookmarks. Pandoc writes a bookmark for every heading, as anchors for a
   table of contents it does not actually generate. Word draws bookmarks as
   grey square brackets whenever "Show bookmarks" is enabled, which makes the
   manuscript look as though every heading is wrapped in [ ].

2. Compatibility mode. Pandoc stamps the file as Microsoft Word 12 (2007), so
   modern Word opens it in Compatibility Mode and disables some features. We
   restamp it and declare compatibility mode 15 (Word 2013+).

3. Line numbers. Elsevier asks for them so that a referee can point at a line
   rather than at a paragraph. Pandoc writes none.

None of this changes content. The first two look wrong to a reviewer opening
the file; the third is asked for at submission.

Usage:
    python scripts/polish_docx.py path/to/file.docx [more.docx ...]
"""

import re
import shutil
import sys
import zipfile
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

COMPAT_BLOCK = (
    '<w:compat>'
    '<w:compatSetting w:name="compatibilityMode" '
    f'w:uri="{W_NS}" w:val="15"/>'
    '</w:compat>'
)


def strip_bookmarks(xml: str) -> tuple[str, int]:
    """Remove w:bookmarkStart / w:bookmarkEnd elements."""
    pattern = re.compile(r"<w:bookmark(?:Start|End)\b[^>]*/>|"
                         r"<w:bookmark(?:Start|End)\b[^>]*>.*?</w:bookmark(?:Start|End)>",
                         re.S)
    n = len(pattern.findall(xml))
    return pattern.sub("", xml), n


def set_modern_app(xml: str) -> str:
    xml = re.sub(r"<Application>.*?</Application>",
                 "<Application>Microsoft Office Word</Application>", xml)
    xml = re.sub(r"<AppVersion>.*?</AppVersion>",
                 "<AppVersion>16.0000</AppVersion>", xml)
    return xml


def set_compat(xml: str) -> str:
    """Declare compatibility mode 15 so Word stops using Compatibility Mode."""
    if "compatibilityMode" in xml:
        return re.sub(r'(<w:compatSetting w:name="compatibilityMode"[^>]*w:val=")\d+(")',
                      r"\g<1>15\g<2>", xml)
    if "<w:compat>" in xml:
        return xml.replace(
            "<w:compat>",
            '<w:compat><w:compatSetting w:name="compatibilityMode" '
            f'w:uri="{W_NS}" w:val="15"/>', 1)
    # No compat block at all: insert one just before the closing settings tag.
    return xml.replace("</w:settings>", COMPAT_BLOCK + "</w:settings>")


def style_tables(path: Path, *, font="Times New Roman", size=10.0) -> int:
    """Give every table the three-rule look journals use.

    Pandoc emits tables with no borders at all, which reads as unformatted,
    and their cells inherit the double line spacing set on Normal, which makes
    them tower over the surrounding text. This applies the convention used in
    printed tables: a rule above the header, a rule below it, a rule under the
    last row, and nothing else — no vertical lines, no interior horizontal
    lines — with the body set single-spaced and one size down from the text.
    """
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    def edge(name, val, sz):
        e = OxmlElement(f"w:{name}")
        e.set(qn("w:val"), val)
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        return e

    doc = Document(path)
    styled = 0
    for table in doc.tables:
        # Single-cell tables are call-out boxes, not data tables. Ruling them
        # and bolding their first row would wreck the design.
        if len(table.rows) == 1 and len(table.columns) == 1:
            continue
        styled += 1
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = table._tbl.tblPr

        for old in tblPr.findall(qn("w:tblBorders")):
            tblPr.remove(old)
        borders = OxmlElement("w:tblBorders")
        borders.append(edge("top", "single", 12))       # rule above header
        borders.append(edge("bottom", "single", 12))    # rule below last row
        for side in ("left", "right", "insideH", "insideV"):
            borders.append(edge(side, "none", 0))
        tblPr.append(borders)

        # Breathing room inside cells; without it the rules sit on the text.
        margins = OxmlElement("w:tblCellMar")
        for side, w in (("top", 60), ("bottom", 60), ("left", 90), ("right", 90)):
            m = OxmlElement(f"w:{side}")
            m.set(qn("w:w"), str(w))
            m.set(qn("w:type"), "dxa")
            margins.append(m)
        for old in tblPr.findall(qn("w:tblCellMar")):
            tblPr.remove(old)
        tblPr.append(margins)

        for r, row in enumerate(table.rows):
            for cell in row.cells:
                if r == 0:
                    tcPr = cell._tc.get_or_add_tcPr()
                    for old in tcPr.findall(qn("w:tcBorders")):
                        tcPr.remove(old)
                    tcb = OxmlElement("w:tcBorders")
                    tcb.append(edge("bottom", "single", 6))   # rule under header
                    tcPr.append(tcb)
                for p in cell.paragraphs:
                    pf = p.paragraph_format
                    pf.line_spacing = 1.0
                    pf.space_before = Pt(1)
                    pf.space_after = Pt(1)
                    for run in p.runs:
                        run.font.name = font
                        run.font.size = Pt(size)
                        if r == 0:
                            run.font.bold = True
    doc.save(path)
    return styled


def add_line_numbers(path: Path, *, restart="continuous", distance=360) -> int:
    """Number the lines continuously, so referees can cite one.

    Word's schema fixes the order of the children of sectPr: lnNumType belongs
    after pgBorders and before pgNumType. Appending it instead leaves a file
    Word reports as corrupt, so it is inserted ahead of whichever of the later
    elements appears first.
    """
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    followers = ("w:pgNumType", "w:cols", "w:formProt", "w:vAlign",
                 "w:noEndnote", "w:titlePg", "w:textDirection", "w:bidi",
                 "w:rtlGutter", "w:docGrid", "w:printerSettings")

    doc = Document(path)
    numbered = 0
    for section in doc.sections:
        sectPr = section._sectPr
        for old in sectPr.findall(qn("w:lnNumType")):
            sectPr.remove(old)
        ln = OxmlElement("w:lnNumType")
        ln.set(qn("w:countBy"), "1")
        ln.set(qn("w:restart"), restart)
        ln.set(qn("w:distance"), str(distance))
        anchor = next((sectPr.find(qn(tag)) for tag in followers
                       if sectPr.find(qn(tag)) is not None), None)
        if anchor is None:
            sectPr.append(ln)
        else:
            anchor.addprevious(ln)
        numbered += 1
    doc.save(path)
    return numbered


def polish(path: Path) -> None:
    lock = path.parent / f"~${path.name[2:]}"
    if lock.exists():
        sys.exit(f"{path.name} appears to be open in Word ({lock.name} present). "
                 "Close it first, or your next save will overwrite this fix.")

    tmp = path.with_suffix(".polished.docx")
    removed = 0
    with zipfile.ZipFile(path) as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                text, removed = strip_bookmarks(data.decode("utf-8"))
                data = text.encode("utf-8")
            elif item.filename == "docProps/app.xml":
                data = set_modern_app(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/settings.xml":
                data = set_compat(data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)
    n_tables = style_tables(path)
    n_blank = drop_empty_paragraphs(path)
    n_sections = add_line_numbers(path)
    print(f"  removed {n_blank} empty paragraphs")
    audit(path)
    print(f"{path.name}: {removed} bookmarks removed, {n_tables} tables styled, "
          f"line numbers on {n_sections} section(s), stamped as Word 16")


def drop_empty_paragraphs(path: Path) -> int:
    """Delete blank paragraphs left behind by the markdown conversion.

    The horizontal rules used as section separators in the source, and the
    blank lines around them, survive as empty paragraphs. At double spacing
    each one opens a visible gap. The final paragraph of a section is left
    alone because it can carry the section properties.
    """
    from docx import Document
    from docx.oxml.ns import qn

    doc = Document(path)
    body = doc.element.body
    removed = 0
    for p in list(body.findall(qn("w:p"))):
        if "".join(p.itertext()).strip():
            continue
        if p.find(qn("w:pPr")) is not None and \
           p.find(qn("w:pPr")).find(qn("w:sectPr")) is not None:
            continue                      # holds section properties
        if p.findall(qn("w:r")) and any(
                r.findall(qn("w:drawing")) or r.findall(qn("w:pict"))
                for r in p.findall(qn("w:r"))):
            continue                      # holds an image
        body.remove(p)
        removed += 1
    doc.save(path)
    return removed


def audit(path: Path) -> None:
    """Report anything left that would look wrong to a reviewer.

    Checks the things that actually go astray when a document is assembled by
    a converter: body text set at some size other than 12pt, stray fonts,
    paragraphs whose spacing was never resolved, and empty paragraphs left
    behind by removed blocks.
    """
    from docx import Document
    from docx.shared import Pt

    doc = Document(path)
    sizes, fonts, spacings = {}, {}, {}
    empties = 0

    for p in doc.paragraphs:
        if not p.text.strip():
            empties += 1
            continue
        ls = p.paragraph_format.line_spacing
        spacings[ls] = spacings.get(ls, 0) + 1
        for run in p.runs:
            if run.font.size is not None:
                pt = run.font.size.pt
                sizes[pt] = sizes.get(pt, 0) + 1
            if run.font.name:
                fonts[run.font.name] = fonts.get(run.font.name, 0) + 1

    normal = doc.styles["Normal"]
    print(f"  body style     : {normal.font.name} {normal.font.size.pt}pt, "
          f"line spacing {normal.paragraph_format.line_spacing}")
    if sizes:
        odd = {k: v for k, v in sizes.items() if k != normal.font.size.pt}
        print(f"  run font sizes : {sizes}"
              + (f"   <-- differs from body: {odd}" if odd else ""))
    if fonts:
        print(f"  run fonts      : {fonts}")
    if spacings:
        print(f"  line spacings  : {spacings}")
    print(f"  empty paragraphs: {empties}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        polish(Path(arg))
