# Comrade

Post to Mastodon with media attachments.

## Install

```bash
pip install git+https://github.com/aayars/comrade@main
```

## Config

Create a `config.json`:

```json
{
  "mastodon_token": "your-access-token",
  "mastodon_instance": "https://mastodon.social"
}
```

## Usage

```bash
post-media --config config.json --status "Hello world"
post-media --config config.json --image photo.jpg --alt "A photo" --status "Check this out"
post-media --config config.json --image one.jpg,two.jpg --status "Multiple images"
```
