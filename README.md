# latex2svg

Python wrapper and CLI utility to render LaTeX markup and equations as SVG using
[dvisvgm](https://dvisvgm.de/) and [svgo](https://github.com/svg/svgo).

Based on the [original work](https://github.com/tuxu/latex2svg) by Tino Wagner, this version has enhanced features.

The **design goals** are:

- **Auto vertical alignment** without any further styling.
  - by adding a `style="vertical-align:"` to the SVG attributes
- **Auto scaling** on font size/zoom change.
  - by using `em` units for `width`, `height` and `style`
- **Unique IDs** so multiple SVGs on one page won’t corrupt each other.
  - by generating random 4-character ID prefixes within the SVG
- **Minified SVG** for direct inclusion.
  - by using `svgo` (a Node app)
- For **_e-book readers_** and **_dictionaries_**:
  - Good legibility.
  - Direct inclusion as `<svg>`, not necessarily `<img>`.
  - Possibility for easy CSS styling, i.e. using `fill`.
  - Compatibility with [`pyglossary`](https://github.com/ilius/pyglossary) and the [ebook-reader-dict](https://github.com/BoboTiG/ebook-reader-dict) project.
  - Possibility of LaTeX preamble changes/additions, to correct LaTeX code in automated processes like converting a Wiktionary dump to an e-reader dictionary.
  - See [examples/screenshots.md](examples/screenshots.md) for a real-life example.

## Usage

### Python 3 module

```python
from latex2svg import latex2svg
out = latex2svg(r'$\sin(x) = \sum_{n=0}^{\infty} \dots$')
print(out['valign'])  # baseline position in em
print(out['svg'])  # rendered SVG
```

### CLI utility

```
$ ./latex2svg.py --help
usage: latex2svg.py [-h] [--version] [--preamble PREAMBLE]

Render LaTeX code from stdin as SVG to stdout. Writes metadata (baseline
position, width, height in em units) into the SVG attributes.

optional arguments:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  --preamble PREAMBLE  LaTeX preamble code to read from file

$ echo '$\sin(x) = \sum_{n=0}^{\infty} \dots$' | ./latex2svg.py > sample.svg
```

Result:

<img src="https://cdn.rawgit.com/Moonbase59/latex2svg/master/sample.svg" style="height: 1.061594em; vertical-align: -0.313097em;" alt="sample formula" />

### Internal vs. external SVG usage

Using SVGs as _inline SVG_ should work perfectly well in all cases.

Should you need to include SVGs as an _external_ HTML `<img>`, you _must_ include <i>latex2svg</i>’s computed <code>valign</code> value
in the <code>&lt;img&gt;</code> tag as a <code>style="vertical-align: …"</code> attribute to achieve correct alignment.
The SVG won’t be stylable using a CSS <code>fill</code> in this case.

```html
<img src="density.svg" style="vertical-align:-.600321em">
```
**This is _not_ a limitation of `latex2svg`.**

## Requirements

- Python 3
- A working LaTeX installation, like _Tex Live_ or _MacTeX_
- [dvisvgm](https://dvisvgm.de/)
- [svgo](https://github.com/svg/svgo)

## License

This project is licensed under the MIT license. See [LICENSE](LICENSE) for
details.

Copyright © 2022 Matthias C. Hormann
