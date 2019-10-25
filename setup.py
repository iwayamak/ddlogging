#!/usr/bin/env python

import os
import shutil
import sys

import ddlogging.handler

from setuptools import Command, find_packages, setup


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel upload")
    sys.exit()


class UploadCommand(Command):

    def run(self):
        try:
            cwd = os.path.join(os.path.abspath(os.path.dirname(__file__)))
            shutil.rmtree(os.path.join(cwd, 'dist'))
        except FileNotFoundError:
            pass

        os.system('twine upload dist/*')
        os.system('git tag v{0}'.format(ddlogging.handler.__version__))
        os.system('git push --tags')
        sys.exit()


setup_options = dict(
    name='ddlogging',
    version=ddlogging.handler.__version__,
    description='Datadog Logs logging handler and utilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Katsuya Iwayama',
    author_email='iwayamak@matsubabreak.com',
    url='https://github.com/iwayamak/ddlogging',
    packages=find_packages(exclude=['tests*', 'test', 'register']),
    license="MIT License",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    keywords='datadog logs logging handler',
)

setup(**setup_options)
