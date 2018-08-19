# Comrade


## Comrade is good ~~Twitter~~ Mastodon bot. Салюд!

This repo is just a set of scripts to post and stream ~~tweets~~ toots from the command line.


## Install

```
/usr/bin/python3 -m venv venv

source venv/bin/activate

pip install git+https://github.com/aayars/comrade

```


## Fuck Twitter

Twitter support is deprecated. When it breaks, it breaks. Let Twitter die.


### Config file

Comrade needs your connection info in a config file. Create a file named `config.json` with the following keys:

```
{
  "api_key": "(deprecated) Your Twitter API key",
  "api_secret": "(deprecated) Your Twitter API secret",
  "access_token": "(deprecated) Your Twitter access token",
  "access_secret": "(deprecated) Your Twitter access secret",
  "mastodon_token": "Your Mastodon access token",
  "mastodon_instance": "Base URL of your Mastodon instance, if not mastodon.social"
}
```

## Scripts

Run a script with `--help` for more info.


### post-media

Post images to Twitter and/or Mastodon (depending on what's in your config file)


### stream-media

Stream image tweets, and handle them with a callback.


### stream-toots

Stream image toots, and handle them with a callback.
