#!/usr/bin/env python3
"""latex2svg

Read LaTeX code from stdin and render a SVG using LaTeX, dvisvgm and svgo.

Returns a minified SVG with `width`, `height` and `style="vertical-align:"`
attribues whose values are in `em` units. The SVG will have (pseudo-)unique
IDs in case more than one is used on the same HTML page.

Based on [original work](https://github.com/tuxu/latex2svg) by Tino Wagner.
"""
__version__ = '0.2.1'
__author__ = 'Matthias C. Hormann'
__email__ = 'mhormann@gmx.de'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2022, Matthias C. Hormann'

import os
import sys
import subprocess
import shlex
import re
from tempfile import TemporaryDirectory
from ctypes.util import find_library

default_template = r"""
\documentclass[{{ fontsize }}pt,preview]{standalone}
{{ preamble }}
\begin{document}
\begin{preview}
{{ code }}
\end{preview}
\end{document}
"""

default_preamble = r"""
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
"""

default_svgo_config = r"""
module.exports = {
  plugins: [
    {
      // use default preset (almost)
      name: 'preset-default',
      params: {
        overrides: {
          // viewbox required to resize SVGs with CSS, disable removal
          removeViewBox: false,
        },
      },
      // enable prefixIds
      name: 'prefixIds',
      params: {
        prefix: '{{ prefix }}',
        delim: '_',
      },
    },
  ],
};
"""

latex_cmd = 'latex -interaction nonstopmode -halt-on-error'
dvisvgm_cmd = 'dvisvgm --no-fonts'
svgo_cmd = 'svgo'

default_params = {
    'fontsize': 12,  # TeX pt
    'template': default_template,
    'preamble': default_preamble,
    'latex_cmd': latex_cmd,
    'dvisvgm_cmd': dvisvgm_cmd,
    'svgo_cmd': svgo_cmd,
    'svgo_config': default_svgo_config,
    'libgs': None,
}


if not hasattr(os.environ, 'LIBGS') and not find_library('gs'):
    if sys.platform == 'darwin':
        # Fallback to homebrew Ghostscript on macOS
        homebrew_libgs = '/usr/local/opt/ghostscript/lib/libgs.dylib'
        if os.path.exists(homebrew_libgs):
            default_params['libgs'] = homebrew_libgs
    if not default_params['libgs']:
        print('Warning: libgs not found', file=sys.stderr)


def latex2svg(code, params=default_params, working_directory=None):
    """Convert LaTeX to SVG using dvisvgm and svgo.

    Parameters
    ----------
    code : str
        LaTeX code to render.
    params : dict
        Conversion parameters.
    working_directory : str or None
        Working directory for external commands and place for temporary files.

    Returns
    -------
    dict
        Dictionary of SVG output and output information:

        * `svg`: SVG data
        * `width`: image width in *em*
        * `height`: image height in *em*
        * `valign`: baseline offset in *em*
    """
    if working_directory is None:
        with TemporaryDirectory() as tmpdir:
            return latex2svg(code, params, working_directory=tmpdir)

    # Caution: TeX & dvisvgm work with TeX pt (1/72.27"), but we need DTP pt (1/72")
    # so we need a scaling factor for correct output sizes
    scaling = 1.00375 # (1/72)/(1/72.27)

    fontsize = params['fontsize']
    document = (params['template']
                .replace('{{ preamble }}', params['preamble'])
                .replace('{{ fontsize }}', str(fontsize))
                .replace('{{ code }}', code))

    with open(os.path.join(working_directory, 'code.tex'), 'w') as f:
        f.write(document)

    # Run LaTeX and create DVI file
    try:
        ret = subprocess.run(shlex.split(params['latex_cmd']+' code.tex'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=working_directory)
        ret.check_returncode()
    except FileNotFoundError:
        raise RuntimeError('latex not found')

    # Add LIBGS to environment if supplied
    env = os.environ.copy()
    if params['libgs']:
        env['LIBGS'] = params['libgs']

    # Convert DVI to SVG
    try:
        ret = subprocess.run(shlex.split(params['dvisvgm_cmd']+' code.dvi'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=working_directory, env=env)
        ret.check_returncode()
    except FileNotFoundError:
        raise RuntimeError('dvisvgm not found')

    # Parse dvisvgm output for size and alignment
    def get_size(output):
        regex = r'\b([0-9.]+)pt x ([0-9.]+)pt'
        match = re.search(regex, output)
        if match:
            return (float(match.group(1)) / fontsize * scaling,
                    float(match.group(2)) / fontsize * scaling)
        else:
            return None, None

    def get_measure(output, name):
        regex = r'\b%s=([0-9.e-]+)pt' % name
        match = re.search(regex, output)
        if match:
            return float(match.group(1)) / fontsize * scaling
        else:
            return None

    output = ret.stderr.decode('utf-8')
    width, height = get_size(output)
    depth = get_measure(output, 'depth')

    # Modify SVG attributes, to a get a self-contained, scaling SVG
    from lxml import etree
    # read SVG, discarding all comments ("<-- Generated by… -->")
    parser = etree.XMLParser(remove_comments=True)
    xml = etree.parse(os.path.join(working_directory, 'code.svg'), parser)
    svg = xml.getroot()
    svg.set('width', f'{width:.6f}em')
    svg.set('height', f'{height:.6f}em')
    svg.set('style', f'vertical-align:{-depth:.6f}em')
    xml.write(os.path.join(working_directory, 'code.svg'))

    # Run svgo to get a minified oneliner with (pseudo-)unique Ids
    # generate random prefix using ASCII letters (ID may not start with a digit)
    import random, string
    prefix = ''.join(random.choice(string.ascii_letters) for n in range(4))
    svgo_config = (params['svgo_config']
                .replace('{{ prefix }}', prefix))

    # write svgo params file
    with open(os.path.join(working_directory, 'svgo.config.js'), 'w') as f:
        f.write(svgo_config)

    try:
        ret = subprocess.run(shlex.split(params['svgo_cmd']+' code.svg'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=working_directory, env=env)
        ret.check_returncode()
    except FileNotFoundError:
        raise RuntimeError('svgo not found')

    with open(os.path.join(working_directory, 'code.svg'), 'r') as f:
        svg = f.read()

    return {'svg': svg, 'valign': round(-depth,6),
        'width': round(width,6), 'height': round(height,6)}


def main():
    """Simple command line interface to latex2svg.

    - Read from `stdin`.
    - Write SVG to `stdout`.
    - On error: write error messages to `stderr` and return with error code.
    """
    import json
    import argparse
    parser = argparse.ArgumentParser(description="""
    Render LaTeX code from stdin as SVG to stdout. Writes metadata (baseline
    offset, width, height in em units) into the SVG attributes.
    """)
    parser.add_argument('--version', action='version',
                    version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument('--preamble',
                        help="LaTeX preamble code to read from file")
    args = parser.parse_args()
    preamble = default_preamble
    if args.preamble is not None:
        with open(args.preamble) as f:
            preamble = f.read()
    latex = sys.stdin.read()
    try:
        params = default_params.copy()
        params['preamble'] = preamble
        out = latex2svg(latex, params)
        sys.stdout.write(out['svg'])
    except subprocess.CalledProcessError as exc:
        # LaTeX prints errors on stdout instead of stderr (stderr is empty),
        # dvisvgm to stderr, so print both (to stderr)
        print(exc.output.decode('utf-8'), file=sys.stderr)
        print(exc.stderr.decode('utf-8'), file=sys.stderr)
        sys.exit(exc.returncode)


if __name__ == '__main__':
    main()
