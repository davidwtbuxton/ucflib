from __future__ import unicode_literals
from distutils.core import setup
import ucf

setup(
    name = 'UCFlib',
    version = ucf.__version__,
    description = 'a library for reading and writing Universal Container Format files',
    author = 'David Buxton',
    author_email = 'david@gasmark6.com',
    py_modules = ['ucf'],
)

