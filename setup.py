#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='comrade',
      version='0.5.0',
      description='Comrade is good Mastodon bot. Салюд!',
      author='Alex Ayars',
      author_email='aayars@gmail.com',
      url='http://github.com/aayars/comrade/',
      packages=find_packages(),

      entry_points='''
        [console_scripts]
        post-media=comrade.scripts.post_media:main
        ''',

      install_requires=[
        "click==8.1.7",
        "cryptography==42.0.5",  # pinned because setuptools is stunad
        "loguru==0.7.0",
        "Mastodon.py==1.8.1",
        ]
      )
