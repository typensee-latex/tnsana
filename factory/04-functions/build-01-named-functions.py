#! /usr/bin/env python3

import re

from collections import defaultdict
from itertools import product

from mistool.os_use import PPath
from mistool.string_use import between, joinand
from orpyste.data import ReadBlock


# ------------------------ #
# -- INTERNAL CONSTANTS -- #
# ------------------------ #

BASENAME = PPath(__file__).stem.replace("build-", "")
BASENAME = BASENAME.replace("[slow]", "")

THIS_DIR = PPath(__file__).parent
STY_FILE = THIS_DIR / f'{BASENAME}.sty'
TEX_FILE = STY_FILE.parent / (STY_FILE.stem + "[fr].tex")

PATTERN_FOR_PEUF = re.compile("\d+-(.*)")
match            = re.search(PATTERN_FOR_PEUF, STY_FILE.stem)
PEUF_FILE        = STY_FILE.parent / (match.group(1).strip() + ".peuf")


TEMP_LATEX_PARAM_FUNC = """
\\let\\std{name}\\{name}
\\renewcommand\\{name}[1][]{{%
    \\std{name}%
    \\if\\relax\\detokenize{{#1}}\\relax\\else%
        _{{#1}}%
    \\fi%
}}
""".lstrip()


DECO = " "*4


# -------------------------- #
# -- THE CONSTANTS TO ADD -- #
# -------------------------- #

with ReadBlock(
    content = PEUF_FILE,
    mode    = "keyval:: ="
) as data:
    functions = data.mydict("std mini")

    for k, v in functions['no-parameter'].items():
        if not v:
            functions['no-parameter'][k] = k

    for k, v in functions['parameter'].items():
        nbparam, desc = v.split(";")

        functions['parameter'][k] = {
            'nbparam': nbparam.strip(),
            'desc'   : desc.strip(),
        }


# ------------------------------ #
# -- LATEX TEMPLATE TO UPDATE -- #
# ------------------------------ #

with open(
    file     = STY_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as styfile:
    temp_sty = styfile.read()


with open(
    file     = TEX_FILE,
    mode     = 'r',
    encoding = 'utf-8'
) as docfile:
    temp_tex = docfile.read()


# --------------------- #
# -- UPDATING MACROS -- #
# --------------------- #

text_start, _, text_end = between(
    text = temp_sty,
    seps = [
        "% Classical functions - START",
        "% Classical functions - END"
    ],
    keepseps = True
)

macro_defs = [
    "\n".join(
        r"\DeclareMathOperator{{\{0}}}{{\operatorname{{{1}}}}}".format(
            latexname,
            humanname
        )
        for latexname, humanname in functions['no-parameter'].items()
    ),
    "",
    "\n".join(
        TEMP_LATEX_PARAM_FUNC.format(name = name)
        for name in functions['parameter']
    )
]

macro_defs = "\n".join(macro_defs)
macro_defs = macro_defs.strip()

temp_sty = f"{text_start}\n\n{macro_defs}\n\n{text_end}"


# ------------------------------ #
# -- UPDATING SUMMARING TABLE -- #
# ------------------------------ #

text_start, _, text_end = between(
    text = temp_tex,
    seps = [
        "% Table of all - START",
        "% Table of all - END"
    ],
    keepseps = True
)


tablefuncs = [
    f"{name} x"
    for name in list(functions['no-parameter'])
]

for name in list(functions['parameter']):
    tablefuncs += [
        f"{name} x",
        f"{name}[p] x",
        ""
    ]


maxsizes = [0]*3

for i in range(len(tablefuncs) // 3):
    for j, texcode in enumerate(tablefuncs[3*i: 3*i+3]):
        l = len(texcode)

        if l > maxsizes[j]:
            maxsizes[j] = l


tabletex = []

for i in range(len(tablefuncs) // 3):
    oneline = []

    for j, texcode in enumerate(tablefuncs[3*i: 3*i+3]):
        if texcode:
            texcode = f"{texcode:{maxsizes[j]}}"
            texcode = f"\\verb#\\{texcode}# : $\\{texcode}$"

        oneline.append(texcode)

    tabletex.append(" & ".join(oneline))


tabletex = '\n\\\\[.75ex]\n'.join(tabletex)

tableformat = "p{0.3\\linewidth}"*3

temp_tex = f"""{text_start}
\\begin{{longtable}}{{{tableformat}}}
{tabletex}
\\end{{longtable}}
{text_end}"""


# ----------------------------------------------- #
# -- UPDATING LISTS FOR THE DOC - NO PARAMETER -- #
# ----------------------------------------------- #

text_start, _, text_end = between(
    text = temp_tex,
    seps = [
        "% List of functions without parameter - START",
        "% List of functions without parameter - END"
    ],
    keepseps = True
)

docinfos   = []
lastmacros = []
lastfirst  = ""
lastlenght = -1

for onemacro in list(functions['no-parameter'].keys()) + ["ZZZZ-unsed-ZZZZ"]:
    if lastfirst:
        if lastfirst != onemacro[0] \
        or lastlenght != len(onemacro):
            lastmacros = ", ".join(lastmacros)

            if lastfirst == "f":
                extra = "\\hfill \\mwhyprefix{{f}}{{rench}}"

            else:
                extra = ""

            docinfos += [
                f"""
\\foreach \\k in {{{lastmacros}}}{{

    \\IDope{{\k}} {extra}
}}
                """,
                "\\separation"
                ""
            ]

            lastfirst  = onemacro[0]
            lastlenght = len(onemacro)
            lastmacros = []

    else:
        lastfirst  = onemacro[0]
        lastlenght = len(onemacro)

    lastmacros.append(onemacro)


if docinfos:
# Let's remove the lase separation.
    docinfos = "\n".join(docinfos[:-1])
    docinfos = docinfos.strip()
    docinfos = f"\n{docinfos}\n"

else:
    docinfos = ""

temp_tex = f"{text_start}\n{docinfos}\n{text_end}"



# --------------------------------------------- #
# -- UPDATING LISTS FOR THE DOC - PARAMETERS -- #
# --------------------------------------------- #

text_start, _, text_end = between(
    text = temp_tex,
    seps = [
        "% List of functions with parameters - START",
        "% List of functions with parameters - END"
    ],
    keepseps = True
)

docinfos = []

for name, infos in functions['parameter'].items():
    nbparam = int(infos['nbparam'])

    if name not in ["ln", "log"]:
        docinfos.append("\\separation")

    if name in ["ln", "lg"]:
        name += " "

    docinfos.append(f"\\IDmacro[o]{{{name}}}{{{nbparam}}}")

    if name.strip() not in ["lg", "ln"]:
        desc = infos["desc"]
        docinfos.append(f"\\IDoption{{}} {desc}")


if docinfos:
    docinfos.append("")
    docinfos = [""] + docinfos[1:]
    docinfos = "\n\n".join(docinfos)
    docinfos = docinfos.strip()
    docinfos = f"\n{docinfos}\n"

else:
    docinfos = ""

temp_tex = f"{text_start}\n{docinfos}\n{text_end}"


# -------------------------- #
# -- UPDATES OF THE FILES -- #
# -------------------------- #

with open(
    file     = TEX_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(temp_tex)

with open(
    file     = STY_FILE,
    mode     = 'w',
    encoding = 'utf-8'
) as docfile:
    docfile.write(temp_sty)
