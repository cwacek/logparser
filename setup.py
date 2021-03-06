import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name='logparser',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        'argparse',
        'progressbar',
        'pyyaml'
    ],
    entry_points={
        'console_scripts': [
            'logparser = logparser.cmdline:script_run'
        ]
    },
    license='MIT',
    description='Generic log parsing framework'
)
