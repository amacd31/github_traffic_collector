import os
from io import open

import versioneer

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

requirements = [
        'phildb',
        'prompt_toolkit',
        'requests',
        'pyyaml',
    ]

setup(
    name='github_traffic_collector',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Collect Github traffic data into a PhilDB database',
    long_description=long_description,
    author='Andrew MacDonald',
    author_email='andrew@maccas.net',
    license='BSD',
    url='https://github.com/amacd31/github_traffic_collector',
    install_requires=requirements,
    packages = ['github_traffic_collector'],
    test_suite = 'nose.collector',
    tests_require = ['nose'],
    entry_points = {
        'console_scripts': [
            'gtc = github_traffic_collector.gtc:main',
            'gtc-server = github_traffic_collector.server:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: System :: Logging',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
