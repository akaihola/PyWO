#from distutils.core import setup, find_packages
from setuptools import setup, find_packages

setup(
    name='PyWO',
    version='0.3',
    author="Wojciech 'KosciaK' Pietrzok",
    author_email='kosciak@kosciak.net',
    packages=find_packages(exclude=['tests', 'tests.*']),
    data_files=[
        ('/etc/pywo', ['etc/pyworc']),
        ('/etc/pywo/layouts', ['etc/layouts/grid_2x2', 'etc/layouts/grid_3x2', 'etc/layouts/grid_3x3',]),
    ],
    scripts = ['bin/pywo'],
    url='http://code.google.com/p/pywo/',
    license='GPL v3',
    description='PyWO allows you to easily organize windows on the desktop using keyboard shortcuts.',
    long_description=open('README').read(),
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: POSIX :: Linux",
        "Topic :: Desktop Environment :: Window Managers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
)

