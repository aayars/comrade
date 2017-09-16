#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='comrade',
      version='0.0.1',
      description='Comrade is good Twitter bot. Салюд!',
      author='Alex Ayars',
      author_email='aayars@gmail.com',
      url='http://github.com/aayars/comrade/',
      packages=find_packages(),

      entry_points='''
        [console_scripts]
        post-media=comrade.scripts.post_media:main
        ''',

      install_requires=[
        "click==6.7",
        "twython==3.6.0",
        ]
      )
