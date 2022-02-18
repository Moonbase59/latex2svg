#!/usr/bin/env python3

from setuptools import setup
from latex2svg import VERSION

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(name='latex2svg',
    version=VERSION,
    description='Render a SVG using LaTeX, dvisvgm and scour',
    long_description_content_type="text/markdown",
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Pre-processors',
        'Topic :: Utilities',
    ],
    keywords='latex converter math formula svg optimizer',
    url='http://github.com/Moonbase59/latex2svg',
    author='Matthias C. Hormann',
    author_email='mhormann@gmx.de',
    license='MIT',
    packages=['latex2svg'],
    entry_points = {
        'console_scripts': ['latex2svg=latex2svg:main'],
    },
    python_requires='>=3',
    install_requires=[
        'lxml',
        ],
    zip_safe=False)
