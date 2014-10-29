# encoding: utf8

import setuptools
from os.path import join, dirname

setuptools.setup(
    name="querystream",
    version="0.0.3",
    py_modules=["querystream"],
    author=u"Paweł Stiasny",
    author_email="pawelstiasny@gmail.com",
    url="http://github.com/pstiasny/querystream",
    license="MIT",
    description="Offline implementation of the Django QuerySet.",
    keywords=['django'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Database',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
