#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='comrade',
      version='0.3.0',
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
        "click==6.7",
        "cryptography==2.5",  # hate this fucking module
        "diskcache==3.1.1",
        "loguru==0.4.1",
        "twython==3.8.2",
        "Mastodon.py==1.5.1",
        "SQLAlchemy==1.2.16",
        ]
      )
