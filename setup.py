from setuptools import setup, find_packages
import sys, os

version = '0.1'

try:
    from mercurial import ui, hg, error
    repo = hg.repository(ui.ui(), ".")
    ver = repo[version]
except ImportError:
    pass
except error.RepoLookupError:
    tip = repo["tip"]
    version = version + ".%s.%s" % (tip.rev(), tip.hex()[:12])
except error.RepoError:
    pass

setup(
    name='sword2',
    version=version,
    description="SWORD v2 python client",
    long_description="""\
SWORD v2 python client""",
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Web Environment",
        #"Framework :: Paste",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="sword-app atom sword2 http",
    author="Ben O'Steen",
    author_email='bosteen@gmail.com',
    url="http://swordapp.org/",
    license='MIT',
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
