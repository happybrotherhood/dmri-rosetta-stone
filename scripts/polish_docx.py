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

Neither affects content, but both look wrong to a reviewer opening the file.

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
    print(f"{path.name}: {removed} bookmarks removed, stamped as Word 16")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        polish(Path(arg))
