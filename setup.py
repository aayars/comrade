#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='comrade',
      version='0.1.0',
      description='Comrade is good Mastodon bot. Салюд!',
      author='Alex Ayars',
      author_email='aayars@gmail.com',
      url='http://github.com/aayars/comrade/',
      packages=find_packages(),

      entry_points='''
        [console_scripts]
        post-media=comrade.scripts.post_media:main
        stream-media=comrade.scripts.stream_media:main
        stream-toots=comrade.scripts.stream_toots:main
        stream-toots-new=comrade.scripts.stream_toots_new:main
        ''',

      install_requires=[
        "click==6.7",
        "twython==3.6.0",
        "Mastodon.py==1.3.1",
        ]
      )
