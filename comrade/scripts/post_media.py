import json
import mimetypes
import time
from datetime import datetime, timezone

import click
import requests
from loguru import logger


def _parse_images(image, alt):
    if not image:
        return []
    paths = image.split(",")
    alts = alt.split(",") if alt else []
    return [(paths[i], alts[i] if i < len(alts) else "") for i in range(len(paths))]


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


def _bluesky_upload_blob(session, base_url, path):
    mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        response = session.post(
            f"{base_url}/xrpc/com.atproto.repo.uploadBlob",
            headers={"Content-Type": mime_type},
            data=f,
        )
        response.raise_for_status()
        return response.json()["blob"]


def _bluesky_login(session, base_url, handle, password):
    response = session.post(
        f"{base_url}/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password},
    )
    response.raise_for_status()
    data = response.json()
    session.headers["Authorization"] = f"Bearer {data['accessJwt']}"
    return data["did"]


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
@click.option(
    "--target",
    type=click.Choice(["mastodon", "bluesky"]),
    default="mastodon",
)
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
    target="mastodon",
):
    with open(config) as f:
        cfg = json.load(f)

    if log_dir:
        logger.add(f"{log_dir}/comrade.log", retention="7 days")

    if target == "mastodon":
        token = cfg.get("mastodon_token")
        base_url = cfg.get("mastodon_instance", "https://mastodon.social")

        if not token:
            logger.error("mastodon_token not found in config")
            return

        try:
            session = requests.Session()
            session.headers["Authorization"] = f"Bearer {token}"

            media_ids = []
            for path, description in _parse_images(image, alt):
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

    elif target == "bluesky":
        handle = cfg.get("bluesky_handle")
        password = cfg.get("bluesky_password")
        base_url = cfg.get("bluesky_instance", "https://bsky.social")

        if not handle or not password:
            logger.error("bluesky_handle and bluesky_password required in config")
            return

        ignored = []
        if visibility != "public":
            ignored.append(f"--visibility {visibility}")
        if sensitive:
            ignored.append("--sensitive")
        if cw:
            ignored.append("--cw")
        if in_reply_to:
            ignored.append("--in-reply-to")
        if ignored:
            logger.warning("Bluesky does not support {}; ignored", ", ".join(ignored))

        parsed_images = _parse_images(image, alt)

        if len(status) > 300:
            logger.error("Bluesky posts cannot exceed 300 characters ({} given)", len(status))
            raise SystemExit(1)

        if len(parsed_images) > 4:
            logger.error("Bluesky posts cannot have more than 4 images ({} given)", len(parsed_images))
            raise SystemExit(1)

        try:
            session = requests.Session()
            did = _bluesky_login(session, base_url, handle, password)

            record = {
                "$type": "app.bsky.feed.post",
                "text": status,
                "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }

            images = []
            for path, description in parsed_images:
                blob = _bluesky_upload_blob(session, base_url, path)
                images.append({"alt": description, "image": blob})

            if images:
                record["embed"] = {
                    "$type": "app.bsky.embed.images",
                    "images": images,
                }

            response = session.post(
                f"{base_url}/xrpc/com.atproto.repo.createRecord",
                json={
                    "repo": did,
                    "collection": "app.bsky.feed.post",
                    "record": record,
                },
            )
            response.raise_for_status()
            result = response.json()
            logger.info("Posted to Bluesky: {}", result["uri"])

        except Exception as e:
            logger.error("Failed to post: {}", e)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
