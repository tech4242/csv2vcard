import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
  name = 'csv2vcard',
  packages = ['csv2vcard'],
  version = '0.2.1',
  description = 'A library for converting csvs to vCards',
  long_description = README,
  author = 'Nikolay Dimolarov',
  author_email = 'dimolarov@hotmail.com',
  url = 'https://github.com/tech4242/csv2vcard',
  download_url = 'https://github.com/tech4242/csv2vcard/archive/0.2.1.tar.gz',
  keywords = ['csv', 'vcard', 'export'],
  python_requires = '>=3.6',
  classifiers = [
    'Development Status :: 3 - Alpha','License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.6',
    ],
)
