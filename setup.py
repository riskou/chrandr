"""
Setuptools based setup module.
"""

from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
#with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#    long_description = f.read()

setup(
    name='chrandr',
    version='0.2.dev',

    description='Change screen configuration.',
    # long_description=long_description,

    url='https://github.com/riskou/chrandr',
    author='Adrien Gandon',
    # author_email='', # private :)
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',

        # End users who knows shell
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',

        'Operating System :: POSIX :: Linux',
        'Topic :: Utilities',
        'Environment :: X11 Applications :: GTK',
    ],

    keywords='xrandr',

    packages=find_packages(exclude=['docs', 'tests']),

    # TODO Add GTK 3 dependency
    # install_requires=['gtk>=3'],

    package_data={
        'chrandr/ui': ['*.glade']
    },
    entry_points = {
        'gui_scripts': [
            'chrandr = chrandr.simple_gui:main'
        ]
    }
)
