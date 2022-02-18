# latex2svg

Python wrapper and CLI utility to render LaTeX markup and equations as SVG using
[dvisvgm](https://dvisvgm.de/) and [scour](https://github.com/scour-project/scour)
(or optionally [svgo](https://github.com/svg/svgo)).

Based on the [original work](https://github.com/tuxu/latex2svg) by Tino Wagner, this version has enhanced features.

The **design goals** are:

- **Auto vertical alignment** without any further styling.
  - by adding a `style="vertical-align:"` to the SVG attributes
- **Auto scaling** on font size/zoom change.
  - by using `em` units for `width`, `height` and `style`
- **Unique IDs** so multiple SVGs on one page won’t corrupt each other.
  - by generating random 3-character ID prefixes within the SVG
- **Minified SVG** for direct inclusion.
  - by using `scour` (or optionally `svgo`, a Node app)
- For **_e-book readers_** and **_dictionaries_**:
  - Good legibility.
  - Direct inclusion as `<svg>`, not necessarily `<img>`.
  - Possibility for easy CSS styling, i.e. using `fill`.
  - Compatibility with [`pyglossary`](https://github.com/ilius/pyglossary) and the [ebook-reader-dict](https://github.com/BoboTiG/ebook-reader-dict) project.
  - Possibility of LaTeX preamble changes/additions, to correct LaTeX code in automated processes like converting a Wiktionary dump to an e-reader dictionary.
  - See [examples/screenshots.md](examples/screenshots.md) for a real-life example.

**Note:** This tool is intended to produce _inline SVGs_, so the _XML prolog_
normally found in standard SVG files gets _stripped_ per default.

Should you need the SVG for other purposes that require the XML prolog, just add
```xml
<?xml version="1.0" encoding="UTF-8"?>
```
as the first line in the file.

## Installation

As long as the [_PyPI_ name issue](https://github.com/pypa/pypi-support/issues/1699)
is unresolved, just install directly from this repository:

```bash
pip3 install git+https://github.com/Moonbase59/latex2svg.git#egg=latex2svg
```

Should your `pip` or setuptools be an older version, or you just prefer to have
the source code on your machine, you can use

```bash
git clone https://github.com/Moonbase59/latex2svg.git
cd latex2svg
pip3 install . -U
```
to install it (including the CLI utility `latex2svg`).


## Usage

### Python 3 module

```python
from latex2svg import latex2svg
out = latex2svg(r'$\sin(x) = \sum_{n=0}^{\infty} \dots$')
print(out['valign'])  # baseline offset in em
print(out['svg'])  # rendered SVG
```

### CLI utility

```
$ latex2svg --help
usage: latex2svg [-h] [--version] [--preamble PREAMBLE]
                 [--optimizer {scour,svgo,none}] [--scale SCALE]

Render LaTeX code from stdin as SVG to stdout. Writes metadata (baseline
offset, width, height in em units) into the SVG attributes.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --preamble PREAMBLE   LaTeX preamble code to read from file
  --optimizer {scour,svgo,none}
                        SVG optimizer to use (default: scour)
  --scale SCALE         SVG output scaling (default: 1.000000)

$ echo '$\sin(x) = \sum_{n=0}^{\infty} \dots$' | latex2svg > sample.svg
```

Result:

<img src="https://cdn.rawgit.com/Moonbase59/latex2svg/master/sample.svg" style="height: 1.061594em; vertical-align: -0.313097em;" alt="sample formula" />

### Changing the default LaTeX preamble

In case you want to change it using `--preamble`, here is the built-in _default preamble_:

```latex
\usepackage[utf8x]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{amstext}
\usepackage{newtxtext}
\usepackage[libertine]{newtxmath}
% prevent errors from old font commands
\DeclareOldFontCommand{\rm}{\normalfont\rmfamily}{\mathrm}
\DeclareOldFontCommand{\sf}{\normalfont\sffamily}{\mathsf}
\DeclareOldFontCommand{\tt}{\normalfont\ttfamily}{\mathtt}
\DeclareOldFontCommand{\bf}{\normalfont\bfseries}{\mathbf}
\DeclareOldFontCommand{\it}{\normalfont\itshape}{\mathit}
\DeclareOldFontCommand{\sl}{\normalfont\slshape}{\@nomath\sl}
\DeclareOldFontCommand{\sc}{\normalfont\scshape}{\@nomath\sc}
% prevent errors from undefined shortcuts
\newcommand{\N}{\mathbb{N}}
\newcommand{\R}{\mathbb{R}}
\newcommand{\Z}{\mathbb{Z}}
```

Python module coding example:

```python
import latex2svg
params = latex2svg.default_params
params['preamble'] = r"""
\usepackage[utf8x]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{amstext}
"""
out = latex2svg.latex2svg(r'$\sin(x) = \sum_{n=0}^{\infty} \dots$', params)
with open('sample2.svg', 'w') as f:
    f.write(out['svg'])
```

### Inline vs. external SVG usage

Using SVGs as _inline SVG_ should work perfectly well in all cases.

Should you need to include SVGs as an _external_ HTML `<img>`, you _must_
include <i>latex2svg</i>’s computed <code>valign</code> value in the
<code>&lt;img&gt;</code> tag as a <code>style="vertical-align: …"</code>
attribute to achieve correct alignment.
The SVG won’t be stylable using a CSS <code>fill</code> in this case.

*Hint:* You can always find the value later by examining the SVG’s root `style`
attribute.

```html
<img src="density.svg" style="vertical-align:-.600321em">
```
**This is _not_ a limitation of `latex2svg`.**

Python module coding example:

```python
from latex2svg import latex2svg
out = latex2svg(r'$\sin(x) = \sum_{n=0}^{\infty} \dots$')
with open('sample3.svg', 'w') as f:
    f.write(out['svg'])
print('<img src="sample3.svg" style="vertical-align:%.6fem">' % out['valign'])
```

## Requirements

- Python 3
- A working LaTeX installation, like _Tex Live_ or _MacTeX_
- [dvisvgm](https://dvisvgm.de/)
- [scour](https://github.com/scour-project/scour) (preferred and default), **—or—**
- [svgo](https://github.com/svg/svgo)

## Change Log

**0.2.0**

- first public version

**0.2.1**

- some small bug fixes

**0.3.0**, **0.3.1** — 2022-02-14

- Now uses `scour` as default SVG optimizer (instead of `svgo`). This produces
  even smaller SVGs, and it’s "all Python" (`pip3 install scour`).
- The SVG optimizer to be used can now be set via the `--optimizer` command line
  option, or by setting `params['optimizer']` if using this as a Python module.
  Possible values are: `scour` (the default), `svgo` or `none`.

**0.4.0** — 2022-02-16

- Added `--scale` command line option (`params['scale']`) for some rare cases
  where additional scaling is needed. Float, defaults to `1.000000`.
- Bugfix: Set `valign` to zero if dvisvgm returns no depth.

**0.4.1** — 2022-02-18

- Attempt at making this an installable Python Package. Unfortunately, _PyPI_
  refuses the name `latex2svg`, although I couldn’t find a package with this name
  on PyPI. So for now you’ll have to git clone and manually install it.

## License

This project is licensed under the MIT license. See [LICENSE](LICENSE) for
details.

Copyright © 2022 Matthias C. Hormann
