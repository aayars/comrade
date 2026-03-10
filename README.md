# Comrade

Post to Mastodon and Bluesky with media attachments.

## Install

```bash
pip install git+https://github.com/aayars/comrade@main
```

## Config

Create a `config.json` with credentials for your target platform:

### Mastodon

```json
{
  "mastodon_token": "your-access-token",
  "mastodon_instance": "https://mastodon.social"
}
```

### Bluesky

```json
{
  "bluesky_handle": "you.bsky.social",
  "bluesky_password": "your-app-password",
  "bluesky_instance": "https://bsky.social"
}
```

## Usage

```bash
# Mastodon (default)
post-media --config config.json --status "Hello world"
post-media --config config.json --image photo.jpg --alt "A photo" --status "Check this out"
post-media --config config.json --image one.jpg,two.jpg --status "Multiple images"

# Bluesky
post-media --config config.json --target bluesky --status "Hello Bluesky"
post-media --config config.json --target bluesky --image photo.jpg --alt "A photo" --status "Check this out"
```
