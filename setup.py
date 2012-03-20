AUTHOR = 'Chris Dent'
AUTHOR_EMAIL = 'cdent@peermore.com'
NAME = 'tiddlywebplugins.nitor'
DESCRIPTION = 'Climbing Database Thing'
VERSION = '0.0.1'


import os

from setuptools import setup, find_packages


setup(
    namespace_packages = ['tiddlywebplugins'],
    name = NAME,
    version = VERSION,
    description = DESCRIPTION,
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    author = AUTHOR,
    author_email = AUTHOR_EMAIL,
    url = 'http://pypi.python.org/pypi/%s' % NAME,
    platforms = 'Posix; MacOS X; Windows',
    packages = find_packages(exclude=['test']),
    scripts = ['nitor'],
    install_requires = ['setuptools',
        'tiddlyweb',
        'tiddlywebplugins.mysql3',
        'tiddlywebplugins.templates',
        'tiddlywebplugins.markdown',
        'tiddlywebplugins.instancer',
        'selector<0.9'
        ],
    zip_safe = False,
    include_package_data = True,
    license = 'BSD',
    )
