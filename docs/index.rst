.. Comrade documentation master file, created by
   sphinx-quickstart on Sun Jan 13 03:14:24 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Comrade's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Comrade is good Mastodon bot. Салюд!
------------------------------------

Stream and post toots with a simple callback-driven interface.

.. image:: https://travis-ci.com/aayars/comrade.svg?branch=master
   :target: https://travis-ci.com/aayars/comrade
   :alt: Build Status

.. image:: https://readthedocs.org/projects/comrade/badge/?version=latest
   :target: https://comrade.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/docker/build/aayars/comrade.svg
   :target: https://hub.docker.com/r/aayars/comrade
   :alt: Docker Status


Installing and Upgrading
------------------------

.. code-block:: bash

    python3 -m venv comrade

    source comrade/bin/activate

    pip install --upgrade git+https://github.com/aayars/comrade

For subsequent activation of the virtual environment, run `source bin/activate` while in the `comrade` directory. To deactivate, run `deactivate`.


Development
~~~~~~~~~~~

To install Comrade in a dev env:

.. code-block:: bash

    git clone https://github.com/aayars/comrade

    cd comrade

    python3 -m venv venv

    source venv/bin/activate

    python setup.py develop
    python setup.py install_scripts

For subsequent activation of the virtual environment, run `source venv/bin/activate` while in the `comrade` directory. To deactivate, run `deactivate`.

Config
------

Comrade needs your connection info in a config file. Create a file named `config.json` with the following keys:

.. code-block:: json

    {
      "mastodon_token": "Your Mastodon access token",
      "mastodon_instance": "Base URL of your Mastodon instance, if not mastodon.social",

      "api_key": "(deprecated) Your Twitter API key",
      "api_secret": "(deprecated) Your Twitter API secret",
      "access_token": "(deprecated) Your Twitter access token",
      "access_secret": "(deprecated) Your Twitter access secret"
    }


CLI
---

Run a script with :code:`--help` for more info.


post-media
~~~~~~~~~~

Post images to Twitter and/or Mastodon (depending on what's in your config file)


stream-toots
~~~~~~~~~~~~

Stream toots, and handle them with a callback.


stream-offline
~~~~~~~~~~~~~~

Work with offline (queued) toots.


stream-archived
~~~~~~~~~~~~~~~

Work with archived (historical) toots.


String Callbacks
^^^^^^^^^^^^^^^^

Callbacks may be a string containing a command to execute.

Several magic tokens are available to string callbacks. Include them in the command, and they will be swapped out for real values.

- `{filename}`: The media attachment filename, if any.
- `{config}`: The path to the Comrade config file
- `{user}`: The third-party Mastodon user who triggered this callback
- `{id}`: The ID of the toot which triggered this callback, or `None`
- `{visibility}`: The type of toot visibility (`public`, `unlisted`, `private`, or `direct`)
- `{sensitive}`: The string :code:` --sensitive`, or empty. Intended as a flag for `post-media` (see example)

.. code-block:: bash

    #!/usr/bin/env bash

    set -ex

    # Contrived example: Process images from a stream

    # Quote args as shown, in case of empty string values. Don't quote `{sensitive}`, since it's a flag.

    callback_command="your-image-script \"{filename}\" && post-media --config {config} --image your-output.jpg --status \"@{user}\" --in-reply-to \"{id}\" --visibility \"{visibility}\" {sensitive}"

    stream-toots --config configs/mastodon.json --callback "$callback_command" --exclude-user your-user


API
---

See :doc:`api` documentation. The API is unofficial and unstable.

Streaming Classes
~~~~~~~~~~~~~~~~~

- `Streamer`: Stream live toots directly from a server
- `OfflineStreamer`: Stream patiently waiting locally queued toots
- `ArchiveSink`: Stream historical toots from a server
- `ArchiveSource`: Stream historical toots from a local archive

Python Callback
~~~~~~~~~~~~~~~

A Python function may be used instead of a string callback. Python callbacks receive the following parameters:

- `account`: A Mastodon.py User Dict of the user initiating this callback
- `client`: A Mastodon client
- `media_url`: The media attachment URL, if any. (First one only)
- `notif_type`: The type of notification. 'update', 'mention', 'reblog', 'follow' or 'favourite'
- `status`: The Mastodon.py Toot Dict which is the subject of this callback
- `orig_status`: The Mastodon.py Toot Dict which initiated this callback

.. code-block:: python

    def callback(account, client, media_url, notif_type, status, orig_status):
        print('here i am with status id {}'.format(status.get('id')))

        ...

    ###

    streamer = Streamer(callback=callback, ...)

    streamer.process(...)


Docker
------

If running via `Docker`_, mount the config file with the `-v` argument to `docker run`.

This example mounts a directory named `configs`, with `config.json` inside.

.. code-block:: bash

    docker run -v configs:/configs post-media --config /configs/config.json ...


.. _`Docker`: https://hub.docker.com/r/aayars/comrade/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
