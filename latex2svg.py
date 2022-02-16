#!/usr/bin/env python3
"""latex2svg

Read LaTeX code from stdin and render a SVG using LaTeX, dvisvgm and scour.

Returns a minified SVG with `width`, `height` and `style="vertical-align:"`
attribues whose values are in `em` units. The SVG will have (pseudo-)unique
IDs in case more than one is used on the same HTML page.

Based on [original work](https://github.com/tuxu/latex2svg) by Tino Wagner.
"""
__version__ = '0.4.0'
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
dvisvgm_cmd = 'dvisvgm --no-fonts --exact-bbox'
svgo_cmd = 'svgo -i {{ infile }} -o {{ outfile }}'
# scour uses a default "precision" of 5 significant digits
# Good enough? Or should we add "--set-precision=7" (or 8)?
# not a tuple but a long concatenated string:
scour_cmd = ('scour --shorten-ids --shorten-ids-prefix="{{ prefix }}" '
    '--no-line-breaks --remove-metadata --enable-comment-stripping '
    '--strip-xml-prolog -i {{ infile }} -o {{ outfile }}')

default_params = {
    'fontsize': 12,  # TeX pt
    'template': default_template,
    'preamble': default_preamble,
    'latex_cmd': latex_cmd,
    'dvisvgm_cmd': dvisvgm_cmd,
    'scale': 1.0,  # default extra scaling (done by dvisvgm)
    'svgo_cmd': svgo_cmd,
    'svgo_config': default_svgo_config,
    'scour_cmd': scour_cmd,
    'optimizer': 'scour',
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
    # dvisvgm will produce a viewBox in DTP pt but SHOW TeX pt in its output.
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
    dvisvgm_cmd = params['dvisvgm_cmd'] + ' --scale=%f' % params['scale']
    dvisvgm_cmd += ' code.dvi'
    try:
        ret = subprocess.run(shlex.split(dvisvgm_cmd),
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
    # no baseline offset if depth not found
    if depth is None:
        depth = 0.0

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

    # Run optimizer to get a minified oneliner with (pseudo-)unique Ids
    # generate random prefix using ASCII letters (ID may not start with a digit)
    import random, string
    prefix = ''.join(random.choice(string.ascii_letters) for n in range(3))
    svgo_cmd = (params['svgo_cmd']
        .replace('{{ infile }}', 'code.svg')
        .replace('{{ outfile }}', 'optimized.svg'))
    svgo_config = (params['svgo_config']
        .replace('{{ prefix }}', prefix))
    # with scour, input & output files must be different
    scour_cmd = (params['scour_cmd']
        .replace('{{ prefix }}', prefix+'_')
        .replace('{{ infile }}', 'code.svg')
        .replace('{{ outfile }}', 'optimized.svg'))

    if params['optimizer'] == 'scour':
        # optimize SVG using scour (default)
        try:
            ret = subprocess.run(shlex.split(scour_cmd),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 cwd=working_directory, env=env)
            ret.check_returncode()
        except FileNotFoundError:
            raise RuntimeError('scour not found')

        with open(os.path.join(working_directory, 'optimized.svg'), 'r') as f:
            svg = f.read()

    elif params['optimizer'] == 'svgo':
        # optimize SVG using svgo (optional)
        # write svgo params file
        with open(os.path.join(working_directory, 'svgo.config.js'), 'w') as f:
            f.write(svgo_config)

        try:
            ret = subprocess.run(shlex.split(svgo_cmd),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 cwd=working_directory, env=env)
            ret.check_returncode()
        except FileNotFoundError:
            raise RuntimeError('svgo not found')

        with open(os.path.join(working_directory, 'optimized.svg'), 'r') as f:
            svg = f.read()

    else:
        # no optimization, just return SVG
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
    parser.add_argument('--optimizer', choices=['scour', 'svgo', 'none'],
        default='scour',
        help='SVG optimizer to use (default: %(default)s)')
    parser.add_argument('--scale', type=float,
        default=1.0,
        help='SVG output scaling (default: %(default)f)')
    args = parser.parse_args()
    preamble = default_preamble
    if args.preamble is not None:
        with open(args.preamble) as f:
            preamble = f.read()
    latex = sys.stdin.read()
    try:
        params = default_params.copy()
        params['preamble'] = preamble
        params['optimizer'] = args.optimizer
        params['scale'] = args.scale
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
