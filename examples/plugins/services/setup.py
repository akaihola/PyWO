#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Example_services',
    version='0.1',
    author="Wojciech 'KosciaK' Pietrzok",
    description='Example of PyWO services plugins.',
    py_modules=['class_service', 'module_service'],
    entry_points={
        'pywo.services': ['module_service = module_service',
                          'class_service = class_service:Clock'], 
    },
)

