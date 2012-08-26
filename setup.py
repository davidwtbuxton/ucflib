from __future__ import unicode_literals
from distutils.core import setup
import ucf
import os


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name = 'UCFlib',
    version = ucf.__version__,
    author = 'David Buxton',
    author_email = 'david@gasmark6.com',
    py_modules = ['ucf'],

    license = 'MIT',
    url = 'http://github.com/davidwtbuxton/ucflib',
    description = 'a library for reading and writing UCF and EPUB formats',
    long_description = read('README.rst'),
    classifiers = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
    ],
)

