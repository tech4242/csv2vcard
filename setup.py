# Legacy setup.py for older pip versions
# Configuration is now in pyproject.toml

import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

setup(
    name='csv2vcard',
    packages=['csv2vcard'],
    version='0.3.0',
    description='A library for converting CSVs to vCards (vCard 3.0 and 4.0)',
    long_description=README,
    long_description_content_type='text/markdown',
    author='tech4242',
    url='https://github.com/tech4242/csv2vcard',
    keywords=['csv', 'vcard', 'contacts', 'export', 'vcf'],
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Typing :: Typed',
    ],
)
