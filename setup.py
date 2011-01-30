#from distutils.core import setup, find_packages
from setuptools import setup, find_packages

setup(
    name='PyWO',
    version='0.3',
    author="Wojciech 'KosciaK' Pietrzok",
    author_email='kosciak@kosciak.net',
    description='PyWO allows you to easily organize windows on the desktop using keyboard shortcuts.',
    long_description=open('README').read(),
    url='http://code.google.com/p/pywo/',
    license='GPL v3',
    keywords='xlib tiling windows',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Environment :: X11 Applications",
        "Topic :: Desktop Environment :: Window Managers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    packages=find_packages(exclude=['ez_setup', 'tests', 'tests.*']),
    data_files=[
        ('/etc/pywo', ['etc/pyworc']),
        ('/etc/pywo/layouts', ['etc/layouts/grid_2x2', 'etc/layouts/grid_3x2', 'etc/layouts/grid_3x3',]),
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    entry_points={
        'console_scripts':[
            'pywo = pywo.main:run',
        ],
    },
    #scripts = ['bin/pywo'],
)

