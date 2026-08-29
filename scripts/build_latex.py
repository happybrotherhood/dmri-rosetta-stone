"""
build_latex.py
--------------
Build a LaTeX version of the manuscript from article_frontiers.md, with the
figures placed inline at the points where they are discussed rather than
listed as captions at the end.

Vector PDF is used for every generated figure (Figures 1, 3, 4 and the two
supplementary panels), so they stay sharp at any zoom; Figure 2 is a screen
capture and is necessarily raster.

Usage:
    python scripts/build_latex.py          # writes latex/manuscript.tex
    tectonic latex/manuscript.tex          # compiles to latex/manuscript.pdf

Outputs:
    latex/manuscript.tex
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "article_frontiers.md"
OUT_DIR = ROOT / "latex"
OUT_TEX = OUT_DIR / "manuscript.tex"

# Each figure: file, width as a fraction of \textwidth, and the heading it is
# anchored before. Widths are chosen so that tall figures still fit one page.
FIGURES = [
    dict(key="Figure1", file="figures/Figure1.pdf", width=1.0,
         anchor="### Data",
         caption=None),
    dict(key="Figure4", file="figures/Figure4.pdf", width=1.0,
         anchor="### Inter-Tool DTI Metric Agreement",
         caption=None),
    dict(key="Figure3", file="figures/Figure3.pdf", width=0.86,
         anchor="### Non-Physical Tensor Fits",
         caption=None),
    dict(key="Figure2", file="figures/Figure2.png", width=1.0,
         anchor="### Runtime Performance",
         caption=None),
]

PREAMBLE = r"""\documentclass[12pt,a4paper]{article}

% TeX Gyre Termes is metrically identical to Times New Roman. Load it by file
% rather than by name: tectonic ships the font files but does not expose them
% to fontspec's system-font lookup.
\usepackage{fontspec}
\setmainfont{texgyretermes}[
  Extension      = .otf,
  UprightFont    = *-regular,
  BoldFont       = *-bold,
  ItalicFont     = *-italic,
  BoldItalicFont = *-bolditalic ]
\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{calc}
\providecommand{\real}[1]{#1}
\usepackage{array}
\usepackage{caption}
\usepackage{lineno}
\usepackage{textcomp}
\usepackage{microtype}
\usepackage{float}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage{parskip}

% Frontiers asks for continuous line numbering and page numbers for review.
\usepackage{etoolbox}
\linenumbers
% lineno and longtable are mutually incompatible ("No counter 'none' defined"),
% so suspend numbering for the duration of each table.
\AtBeginEnvironment{longtable}{\nolinenumbers}
\AtEndEnvironment{longtable}{\linenumbers}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}

% The figures are large; without these LaTeX defers every one of them to the
% end of the document rather than placing it near the text that discusses it.
\renewcommand{\topfraction}{0.92}
\renewcommand{\bottomfraction}{0.85}
\renewcommand{\textfraction}{0.06}
\renewcommand{\floatpagefraction}{0.72}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{5}

% Numeric tables are tight; stop TeX hyphenating tool names like MRtrix3
% across lines inside a cell, and give the columns a little more room.
\setlength{\tabcolsep}{4pt}

\captionsetup{font=small,labelfont=bf,justification=justified,
              singlelinecheck=false,skip=6pt}
\setcounter{secnumdepth}{0}
\setlength{\parindent}{0pt}
\linespread{1.05}

% pandoc emits \tightlist for compact lists
\providecommand{\tightlist}{%
  \setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}

% Verbatim inside tables needs a breakable column type
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}

\title{\vspace{-2.2cm}\bfseries dMRI Rosetta Stone: An Open-Source Interactive
Platform for Cross-Tool Diffusion MRI Education and Reproducibility}
\author{Busra Mutlu\thanks{Correspondence: Busra Mutlu,
\texttt{[email address]}, Department of Neuroimaging, King's College London,
De Crespigny Park, London SE5 8AF, United Kingdom.}\\[2pt]
\normalsize Department of Neuroimaging, King's College London,
London, United Kingdom}
\date{}

\begin{document}
\maketitle
\thispagestyle{fancy}

\noindent\textbf{Article type:} Technology and Code \\
\textbf{Journal:} Frontiers in Neuroinformatics \\
\textbf{Specialty section:} Methods in Neuroimaging \\
\textbf{Running title:} dMRI Rosetta Stone: Cross-Tool dMRI Education Platform

\vspace{4pt}\hrule\vspace{10pt}

"""

POSTAMBLE = r"""
\end{document}
"""


def extract_captions(md: str) -> dict:
    """Pull the figure captions out of the trailing Figure Captions section."""
    m = re.search(r"^## Figure Captions\s*$(.*?)\Z", md, re.M | re.S)
    if not m:
        return {}
    caps = {}
    # Main figures read "**Figure 3.**"; supplementary ones read
    # "**Supplementary Figure S1.**". Normalise both to FigureN / FigureSN.
    for block in re.finditer(
        r"\*\*(?:Supplementary\s+)?(Figure\s+S?\d+)\.\*\*\s*(.*?)"
        r"(?=\n\*\*(?:Supplementary\s+)?Figure|\Z)",
        m.group(1), re.S,
    ):
        label = block.group(1).replace(" ", "")
        caps[label] = " ".join(block.group(2).split())
    return caps


def md_to_tex(md_fragment: str) -> str:
    """Convert a markdown fragment to LaTeX via pandoc."""
    r = subprocess.run(
        # --no-highlight keeps code blocks as plain verbatim; the syntax
        # colouring pandoc would otherwise emit needs its own preamble
        # (Shaded/Highlighting) and adds nothing to a printed manuscript.
        ["pandoc", "--from", "markdown", "--to", "latex",
         "--wrap=preserve", "--shift-heading-level-by=-1", "--no-highlight"],
        input=md_fragment, capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.exit(f"pandoc failed:\n{r.stderr}")
    return r.stdout


# Characters the Times clone either lacks outright or sets poorly. Superscript
# minus (U+207B) is the dangerous one: the font has no glyph, XeTeX drops it
# silently, and "3.0 x 10^-3" would print as "3.0 x 10^3" — a factual error in
# the text rather than a cosmetic blemish. Everything here is mapped to maths
# or to a proper LaTeX command instead of being left to the font.
UNICODE_FIXES = [
    ("10⁻³", r"$10^{-3}$"),
    ("⁻³", r"$^{-3}$"),
    ("⁻", r"$^{-}$"),
    ("³", r"\textsuperscript{3}"),
    ("²", r"\textsuperscript{2}"),
    ("¹", r"\textsuperscript{1}"),
    ("−", r"$-$"),          # U+2212 true minus, not a hyphen
    ("±", r"$\pm$"),
    ("×", r"$\times$"),
    ("≥", r"$\geq$"),
    ("≤", r"$\leq$"),
    ("≈", r"$\approx$"),
    ("∈", r"$\in$"),
    ("ρ", r"$\rho$"),
    ("σ", r"$\sigma$"),
    ("µ", r"\textmu{}"),
]


def fix_unicode(tex: str) -> str:
    """Map characters the text font cannot set onto LaTeX equivalents."""
    for src, dst in UNICODE_FIXES:
        tex = tex.replace(src, dst)
    return tex


def caption_to_tex(text: str) -> str:
    """Convert one markdown caption to LaTeX.

    Captions bypass the main body conversion, so they need the same treatment:
    without it, emphasis and code spans stay as literal markdown and an
    underscore in a filename such as fslinstaller.py is read as a maths
    subscript, which aborts the compile.
    """
    tex = md_to_tex(text).strip()
    return fix_unicode(tex)


def longtables_to_tabular(tex: str) -> str:
    """Rewrite pandoc's longtable output as plain tabular inside a float.

    Two reasons. First, pandoc emits `\\def\\LTcaptype{none}` for captionless
    tables, which makes the caption package call \\refstepcounter on an
    undefined counter ("No counter 'none' defined"). Second, lineno and
    longtable are mutually incompatible. Every table here is a handful of
    rows and never needs to break across pages, so a tabular sidesteps both.
    """
    pattern = re.compile(
        r"(?:\{\\def\\LTcaptype\{none\}[^\n]*\n)?"      # optional wrapper open
        r"\\begin\{longtable\}\[\]\{(?P<cols>.*?)\}\n"
        r"(?P<body>.*?)"
        r"\\end\{longtable\}\n"
        r"(?:\}\n)?",                                    # optional wrapper close
        re.S,
    )

    def repl(m):
        cols = m.group("cols")
        body = m.group("body")
        # Drop the longtable-only running-header machinery.
        for marker in (r"\endfirsthead", r"\endhead", r"\endlastfoot",
                       r"\endfoot"):
            body = body.replace(marker, "")
        body = body.replace(r"\noalign{}", "")
        # Collapse the blank lines those removals leave behind.
        body = re.sub(r"\n{3,}", "\n\n", body).strip("\n")
        return (
            "\\begin{table}[htbp]\n\\centering\\footnotesize\n"
            "\\hyphenpenalty=10000\\exhyphenpenalty=10000\\relax\n"
            f"\\begin{{tabular}}{{{cols}}}\n{body}\n\\end{{tabular}}\n"
            "\\end{table}\n"
        )

    return pattern.sub(repl, tex)



def attach_table_captions(tex: str) -> str:
    """Pull each "**Table N. ...**" paragraph into the float beneath it.

    In the markdown the caption is an ordinary bold paragraph sitting above
    the table. Left that way it is a separate block of text, so the float
    drifts and the caption is stranded on the previous page. Moving it inside
    the float — as \\caption* so the numbering already in the text is not
    duplicated — keeps the two together. Any italic panel subtitle between
    the caption and the table is carried in as well.
    """
    pattern = re.compile(
        r"(?P<cap>\\textbf\{Table\s+\d+\..*?)\n\n"
        r"(?:(?P<sub>\\emph\{.*?\})\n\n)?"
        r"\\begin\{table\}\[[^\]]*\]\n(?P<inner>.*?)\\end\{table\}\n",
        re.S,
    )

    def repl(m):
        sub = m.group("sub")
        subtitle = f"{sub}\\par\\smallskip\n" if sub else ""
        return (
            "\\begin{table}[H]\n"
            f"\\caption*{{{m.group('cap').strip()}}}\n"
            f"{subtitle}{m.group('inner')}"
            "\\end{table}\n"
        )

    return pattern.sub(repl, tex)


def figure_env(fig: dict, caption: str) -> str:
    """Emit one figure float, pinned to its number.

    The figures are placed where they are discussed, which is not the same as
    their numeric order: brain extraction (Figure 4) is discussed before FA
    agreement (Figure 3). LaTeX numbers floats by order of appearance, so the
    counter is set explicitly before each one to keep the printed number in
    step with the text and with the Word version.
    """
    label = fig["key"]
    n = int(re.search(r"\d+", label).group())
    return (
        "\n\\begin{figure}[tbp]\n"
        "  \\centering\n"
        f"  \\setcounter{{figure}}{{{n - 1}}}\n"
        f"  \\includegraphics[width={fig['width']}\\textwidth]{{{fig['file']}}}\n"
        f"  \\caption{{{caption}}}\n"
        f"  \\label{{fig:{label}}}\n"
        "\\end{figure}\n\n"
    )


def main():
    OUT_DIR.mkdir(exist_ok=True)
    md = SRC.read_text()
    captions = extract_captions(md)
    captions = {k: caption_to_tex(v) for k, v in captions.items()}
    if not captions:
        sys.exit("No figure captions found — has the Figure Captions section moved?")

    # Body runs from the Abstract to just before the trailing caption list.
    start = md.index("## Abstract")
    end = md.index("## Figure Captions")
    body = md[start:end]

    # Drop horizontal rules, which pandoc renders as stray centred lines.
    body = re.sub(r"^---\s*$", "", body, flags=re.M)

    # Splice each figure in ahead of the section that discusses it, so the
    # float lands on or near the right page instead of at the end.
    for fig in FIGURES:
        cap = captions.get(fig["key"])
        if cap is None:
            sys.exit(f"No caption found for {fig['key']}")
        anchor = fig["anchor"]
        if anchor not in body:
            sys.exit(f"Anchor not found for {fig['key']}: {anchor!r}")
        body = body.replace(
            anchor, f"ZZFIGUREZZ{fig['key']}ZZ\n\n{anchor}", 1)

    tex_body = md_to_tex(body)
    tex_body = longtables_to_tabular(tex_body)
    tex_body = fix_unicode(tex_body)
    tex_body = attach_table_captions(tex_body)

    # pandoc passes HTML comments through as raw text; swap them for floats.
    for fig in FIGURES:
        tex_body = tex_body.replace(
            f"ZZFIGUREZZ{fig['key']}ZZ",
            figure_env(fig, captions[fig["key"]]))

    # Supplementary figures go at the very end, after the references.
    supp = ("\n\\clearpage\n\\section*{Supplementary Figures}\n"
        "\\renewcommand{\\thefigure}{S\\arabic{figure}}\n"
        "\\setcounter{figure}{0}\n")
    for key, width in (("FigureS1", 0.86), ("FigureS2", 1.0)):
        supp += figure_env(
            dict(key=key, file=f"figures/{key}.pdf", width=width),
            captions[key])

    OUT_TEX.write_text(PREAMBLE + tex_body + supp + POSTAMBLE)
    print(f"wrote {OUT_TEX}")
    print(f"  figures inlined: {', '.join(f['key'] for f in FIGURES)}")
    print(f"  supplementary:   FigureS1, FigureS2")


if __name__ == "__main__":
    main()
