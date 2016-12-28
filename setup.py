from setuptools import setup, find_packages
import sys, os

version = '0.2.0'

setup(
    name='sword2',
    version=version,
    description="SWORD v2 python client",
    long_description="""\
SWORD v2 python client""",
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
	"License :: OSI Approved :: Apache Software License",
	"Natural Language :: English",
        "Operating System :: OS Independent",
	"Programming Language :: Python :: 2 :: Only",
	"Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="sword-app atom sword2 http",
    author="Ben O'Steen, Cottage Labs",
    author_email='us@cottagelabs.com',
    url="http://swordapp.org/",
    license='Apache',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "httplib2",
    ],
    # Following left in as a memory aid for later-
    #entry_points="""
    #    # -*- Entry points: -*-
    #    [console_scripts]
    #    cmd=module.path:func_name
    #""",
)
