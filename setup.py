import os
from setuptools import setup, find_packages

# single source of truth for package version
version_ns = {}
with open(os.path.join('fair_research_login', 'version.py')) as f:
    exec(f.read(), version_ns)

with open('README.rst') as f:
    long_description = f.read()

install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)

setup(
    name='fair-research-login',
    description='A generalized library for storing native auth tokens',
    long_description=long_description,
    url='https://github.com/fair-research/native-login',
    maintainer='Fair Research',
    maintainer_email='',
    version=version_ns['__version__'],
    packages=find_packages(),
    requires=[],
    install_requires=install_requires,
    dependency_links=[],
    license='Apache 2.0',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ]
)
