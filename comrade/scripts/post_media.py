import json
import mimetypes
import time

import click
import requests
from loguru import logger


def _upload_media(session, base_url, path, description):
    mime_type = mimetypes.guess_type(path)[0]

    with open(path, "rb") as f:
        files = {"file": (path, f, mime_type)}
        data = {"description": description} if description else {}
        response = session.post(f"{base_url}/api/v2/media", files=files, data=data)
        response.raise_for_status()
        result = response.json()

    # v2/media returns 202 while still processing
    if response.status_code == 202:
        media_id = result["id"]
        for _ in range(60):
            time.sleep(1)
            r = session.get(f"{base_url}/api/v1/media/{media_id}")
            if r.status_code == 200:
                return r.json()["id"]
        raise TimeoutError(f"Media {media_id} not processed after 60s")

    return result["id"]


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--image", type=click.Path(dir_okay=False), required=False)
@click.option("--alt", type=str, required=False)
@click.option("--status", type=str, required=True)
@click.option("--in-reply-to", type=str)
@click.option("--sensitive", is_flag=True, default=False)
@click.option("--cw", type=str)
@click.option(
    "--visibility",
    type=click.Choice(["public", "unlisted", "private", "direct"]),
    default="public",
)
@click.option("--log-dir", type=click.Path(dir_okay=True), default=None)
def main(
    config,
    image,
    alt,
    status,
    in_reply_to=None,
    sensitive=False,
    cw=None,
    visibility="public",
    log_dir=None,
):
    with open(config) as f:
        cfg = json.load(f)

    if log_dir:
        logger.add(f"{log_dir}/comrade.log", retention="7 days")

    token = cfg.get("mastodon_token")
    base_url = cfg.get("mastodon_instance", "https://mastodon.social")

    if not token:
        logger.error("mastodon_token not found in config")
        return

    try:
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {token}"

        media_ids = []
        if image:
            alts = alt.split(",") if alt else []
            paths = image.split(",")
            for i, path in enumerate(paths):
                description = alts[i] if i < len(alts) else None
                media_ids.append(_upload_media(session, base_url, path, description))

        payload = {
            "status": status,
            "visibility": visibility,
            "sensitive": sensitive,
        }
        if media_ids:
            payload["media_ids"] = media_ids
        if in_reply_to:
            payload["in_reply_to_id"] = in_reply_to
        if cw:
            payload["spoiler_text"] = cw

        response = session.post(f"{base_url}/api/v1/statuses", json=payload)
        response.raise_for_status()

    except Exception as e:
        logger.error("Failed to post: {}", e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
