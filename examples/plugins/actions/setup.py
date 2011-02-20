#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Example_actions',
    version='0.1',
    author="Wojciech 'KosciaK' Pietrzok",
    description='Example of PyWO actions plugins.',
    py_modules=['example_actions'],
    entry_points={
        'pywo.actions': ['example_actions = example_actions',], 
    },
)

