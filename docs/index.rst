.. Comrade documentation master file, created by
   sphinx-quickstart on Sun Jan 13 03:14:24 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Comrade's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

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
