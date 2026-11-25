"""
uniform_format.py
-----------------
Force one typeface in a .docx: Times New Roman, 12 pt, black, in every run,
every style and the document defaults, headings and tables included. Bold,
italic, underline, strike-through, superscript and subscript are kept, so
headings stay bold and the marked-up manuscript keeps its strike and
underline marks.

The journal does not ask for this, but a package in one typeface reads as
one document, and the pandoc reference styles give headings a colour and a
larger size that look out of place next to the body text.

Usage:
    python scripts/uniform_format.py FILE.docx [FILE.docx ...]
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
FONT = "Times New Roman"
SIZE = "24"          # half-points
COLOR = "000000"

# Child order of w:rPr in the schema; Word refuses files that break it.
RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps",
             "strike", "dstrike", "outline", "shadow", "emboss", "imprint",
             "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing",
             "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
             "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang",
             "eastAsianLayout", "specVanish", "oMath"]


def q(tag):
    return f"{{{W}}}{tag}"


def set_child(rpr, tag, attrs):
    """Set attributes on the child <w:tag> of rpr, creating it in schema order."""
    el = rpr.find(f"w:{tag}", NS)
    if el is None:
        el = etree.Element(q(tag))
        pos = RPR_ORDER.index(tag)
        inserted = False
        for i, child in enumerate(list(rpr)):
            name = etree.QName(child).localname
            if name in RPR_ORDER and RPR_ORDER.index(name) > pos:
                rpr.insert(i, el)
                inserted = True
                break
        if not inserted:
            rpr.append(el)
    for k in list(el.attrib):
        if "Theme" in k or "theme" in k.lower() and k != q("val"):
            del el.attrib[k]
    for k, v in attrs.items():
        el.set(q(k), v)
    return el


def fix_rpr(rpr):
    set_child(rpr, "rFonts", {"ascii": FONT, "hAnsi": FONT, "cs": FONT, "eastAsia": FONT})
    set_child(rpr, "color", {"val": COLOR})
    set_child(rpr, "sz", {"val": SIZE})
    set_child(rpr, "szCs", {"val": SIZE})
    for tag in ("highlight",):
        el = rpr.find(f"w:{tag}", NS)
        if el is not None:
            rpr.remove(el)


def fix_part(xml_bytes, is_styles):
    root = etree.fromstring(xml_bytes)
    n = 0
    for rpr in root.iter(q("rPr")):
        fix_rpr(rpr)
        n += 1
    if is_styles:
        # Document defaults and every style must carry an rPr of their own.
        defaults = root.find("w:docDefaults/w:rPrDefault", NS)
        if defaults is not None and defaults.find("w:rPr", NS) is None:
            defaults.append(etree.Element(q("rPr")))
            fix_rpr(defaults.find("w:rPr", NS))
        for style in root.findall("w:style", NS):
            if style.get(q("type")) in ("paragraph", "character", "table"):
                rpr = style.find("w:rPr", NS)
                if rpr is None:
                    rpr = etree.SubElement(style, q("rPr"))
                    fix_rpr(rpr)
                # Headings keep their weight once colour and size no longer
                # distinguish them from the body text.
                if re.match(r"(?i)heading\d|title$", style.get(q("styleId"), "")):
                    set_child(rpr, "b", {})
                    set_child(rpr, "bCs", {})
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), n


def main(paths):
    for p in map(Path, paths):
        tmp = p.with_suffix(".fmt.docx")
        total = 0
        with zipfile.ZipFile(p) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if re.match(r"word/(document|styles|numbering|footnotes|endnotes|header\d*|footer\d*)\.xml$", item.filename):
                    data, n = fix_part(data, item.filename == "word/styles.xml")
                    total += n
                zout.writestr(item, data)
        shutil.move(tmp, p)
        print(f"{p.name}: {total} run properties set to {FONT} 12 pt black")


if __name__ == "__main__":
    main(sys.argv[1:])
