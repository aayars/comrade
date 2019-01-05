# Comrade


## Comrade is good Mastodon bot. Салюд!

This repo is a set of scripts to post and stream toots from the command line.

Twitter support is deprecated. When it breaks, it breaks forever.

[![Build Status](https://travis-ci.com/aayars/comrade.svg?branch=master)](https://travis-ci.com/aayars/comrade)
[![Docker Build Status](https://img.shields.io/docker/build/aayars/comrade.svg)](https://hub.docker.com/r/aayars/comrade)


## Installing and Upgrading

```
/usr/bin/python3 -m venv venv

source venv/bin/activate

pip install --upgrade git+https://github.com/aayars/comrade

```


## Config

Comrade needs your connection info in a config file. Create a file named `config.json` with the following keys:

```
{
  "mastodon_token": "Your Mastodon access token",
  "mastodon_instance": "Base URL of your Mastodon instance, if not mastodon.social"
  "api_key": "(deprecated) Your Twitter API key",
  "api_secret": "(deprecated) Your Twitter API secret",
  "access_token": "(deprecated) Your Twitter access token",
  "access_secret": "(deprecated) Your Twitter access secret",
}
```

## Scripts

Run a script with `--help` for more info.


### post-media

Post images to Twitter and/or Mastodon (depending on what's in your config file)


### stream-toots

Stream toots from Mastodon, and handle them with a callback.

Several magic tokens are available to string callbacks. Include them in the command, and they will be swapped out for real values.

- `{filename}`: The media attachment filename, if any.
- `{config}`: The path to the comrade config file
- `{user}`: The third-party Mastodon user who triggered this callback
- `{id}`: The ID of the toot which triggered this callback, or `None`
- `{visibility}`: The type of toot visibility (`public`, `unlisted`, `private`, or `direct`)
- `{sensitive}`: The string ` --sensitive`, or empty. Intended as a flag for `post-media` (see example)

```
#!/usr/bin/env bash

set -ex

# Contrived example: Process images from a stream

# Quote args as shown, in case of empty string values. Don't quote `{sensitive}`, since it's a flag.

callback_command="your-image-script \"{filename}\" && post-media --config {config} --image your-output.jpg --status \"@{user}\" --in-reply-to \"{id}\" --visibility \"{visibility}\" {sensitive}"

stream-toots --config configs/mastodon.json --callback "$callback_command" --exclude-user your-user
```


### stream-media

Stream image tweets from Twitter, and handle them with a callback.

```
stream-media --config configs/twitter.json --track @your-user --callback "$callback_command" --exclude-user your-user
```

## Docker

If running via [Docker](https://hub.docker.com/r/aayars/comrade/), mount the config file with the `-v` argument to `docker run`.

This example mounts a directory named `configs`, with `config.json` inside.

```
docker run -v configs:/configs post-media --config /configs/config.json ...
```
