#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='comrade',
      version='0.4.0',
      description='Comrade is good Mastodon bot. Салюд!',
      author='Alex Ayars',
      author_email='aayars@gmail.com',
      url='http://github.com/aayars/comrade/',
      packages=find_packages(),

      entry_points='''
        [console_scripts]
        post-media=comrade.scripts.post_media:main
        stream-toots=comrade.scripts.stream_toots:main
        stream-offline=comrade.scripts.stream_offline:main
        stream-archived=comrade.scripts.stream_archived:main
        ''',

      install_requires=[
        "click==8.1.3",
        "cryptography==41.0.0",  # pinned because setuptools is stunad
        "loguru==0.7.0",
        "twython==3.9.1",
        "Mastodon.py==1.8.1",
        ]
      )
