import os, sys
try:
    from setuptools import setup, find_packages
    use_setuptools = True
except ImportError:
    from distutils.core import setup
    use_setuptools = False

try:
    with open('README.rst', 'rt') as readme:
        description = '\n' + readme.read()
except IOError:
    # maybe running setup.py from some other dir
    description = ''

python_requires='>=3.5'
install_requires = [
    'rx>=3.0',
    'scipy>=1.0',
    'cyclotron>=1.2',
    'cyclotron-aiohttp>=1.0',
    'cyclotron-std>=1.0',
]

setup(
    name="deepspeech-server",
    version='2.2.0',
    url='https://github.com/MainRo/deepspeech-server.git',
    license='MPL-2.0',
    description="server for mozilla deepspeech",
    long_description=description,
    author='Romain Picard',
    author_email='romain.picard@softathome.com',
    packages=find_packages(),
    install_requires=install_requires,
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Artificial Intelligence'
    ],
    scripts=['script/deepspeech-server'],
)
