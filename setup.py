import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name='logparser',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'argparse',
        'progressbar'
    ],
    entry_points={
        'console_scripts': [
            'logparser = logparser:script_run'
        ]
    },
    license='MIT',
    description='Generic log parsing framework'
)
