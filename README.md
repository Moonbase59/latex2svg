# latex2svg

Python wrapper and CLI utility to render LaTeX markup and equations as SVG using
[dvisvgm](https://dvisvgm.de/) and [svgo](https://github.com/svg/svgo).


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

Result: <img src="https://cdn.rawgit.com/Moonbase59/latex2svg/master/sample.svg" style="height: 1.061594em; vertical-align: -0.313097em;" alt="sample formula" />, perfectly aligned (hopefully).

## License

This project is licensed under the MIT license. See [LICENSE](LICENSE) for
details.

Copyright © 2022 Matthias C. Hormann
