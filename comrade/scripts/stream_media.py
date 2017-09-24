import click
import json
import subprocess

from twython import TwythonStreamer

import requests


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--track", type=str, required=True)
@click.option("--callback", type=str, required=True)
@click.option("--exclude-user", type=str)
def main(config, track, callback, exclude_user=None):
    class Streamer(TwythonStreamer):
        def on_success(self, data):
            if data.get("possibly_sensitive"):
                return

            if data.get("rewtweeted_status"):
                return

            user = data.get("user", {}).get("screen_name"):

            if exclude_user and exclude_user == user:
                return

            media_url = data.get("entities", {}).get("media", {}).get("media_url_https")

            if not media_url:
                return
            
	    r = requests.get(media_url, stream=True)

            # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
            with open("tweet.jpg", 'wb') as fh:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk:
                        fh.write(chunk)

            """
	    Process tweet
	    effect_name=`artmangler random {filename}` && post-media --config {config} --image mangled.png --status "{user} vs. $effect_name" --in-reply-to {id}
	    """
            print(callback.format(filename="tweet.jpg", config=config, user=user, id=data["id"]))
            # subprocess.run(callback.format(filename="tweet.jpg", config=config, user=user, id=data["id"]), shell=True, check=True)
            # print(json.dumps(data, indent=4))

        def on_error(self, status_code, data):
            print(status_code)

    cfg = json.load(open(config))

    stream = Streamer(cfg["api_key"], cfg["api_secret"], cfg["access_token"], cfg["access_secret"])
    stream.statuses.filter(track=track)
