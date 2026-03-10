from io import BytesIO, StringIO
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

from comrade.scripts.post_media import _parse_images, main


def test_parse_images():
    """_parse_images splits comma-separated paths and alts."""
    result = _parse_images("a.png,b.png", "first,second")
    assert result == [("a.png", "first"), ("b.png", "second")]


def test_parse_images_missing_alts():
    """_parse_images pads missing alts with empty string."""
    result = _parse_images("a.png,b.png", "only-first")
    assert result == [("a.png", "only-first"), ("b.png", "")]


def test_parse_images_none():
    """_parse_images returns empty list when no images."""
    result = _parse_images(None, None)
    assert result == []


def _mock_open(config_json, files):
    real_open = open

    def side_effect(path, mode="r", *args, **kwargs):
        if path in files:
            return files[path]
        return real_open(path, mode, *args, **kwargs)

    mock = Mock(side_effect=side_effect)

    files.setdefault("config.json", StringIO(config_json))

    return mock


CONFIG_JSON = '{"mastodon_token":"token","mastodon_instance":"https://example"}'


def test_post_media_multiple_images():
    img1 = BytesIO(b"data1")
    img2 = BytesIO(b"data2")

    mock_session = MagicMock()
    mock_session.post.side_effect = [
        MagicMock(status_code=200, json=lambda: {"id": "mid1"}),
        MagicMock(status_code=200, json=lambda: {"id": "mid2"}),
        MagicMock(status_code=200),
    ]

    open_mock = _mock_open(CONFIG_JSON, {"image1.png": img1, "image2.png": img2})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock):
        mock_requests.Session.return_value = mock_session
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--image", "image1.png,image2.png", "--status", "hello"],
        )

    assert result.exit_code == 0
    assert mock_session.post.call_count == 3

    status_call = mock_session.post.call_args_list[2]
    assert status_call[0][0] == "https://example/api/v1/statuses"
    assert status_call[1]["json"]["status"] == "hello"
    assert status_call[1]["json"]["media_ids"] == ["mid1", "mid2"]


def test_post_media_no_image():
    mock_session = MagicMock()
    mock_session.post.return_value = MagicMock(status_code=200)

    open_mock = _mock_open(CONFIG_JSON, {})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock):
        mock_requests.Session.return_value = mock_session
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--status", "text only"],
        )

    assert result.exit_code == 0
    assert mock_session.post.call_count == 1

    status_call = mock_session.post.call_args
    assert status_call[1]["json"]["status"] == "text only"
    assert "media_ids" not in status_call[1]["json"]


def test_post_media_async_upload():
    img1 = BytesIO(b"data1")

    mock_session = MagicMock()
    # v2/media returns 202 (processing)
    mock_session.post.side_effect = [
        MagicMock(status_code=202, json=lambda: {"id": "mid1"}),
        MagicMock(status_code=200),  # status post
    ]
    # Polling GET returns 200 (ready)
    mock_session.get.return_value = MagicMock(status_code=200, json=lambda: {"id": "mid1"})

    open_mock = _mock_open(CONFIG_JSON, {"image1.png": img1})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("comrade.scripts.post_media.time") as mock_time, \
         patch("builtins.open", open_mock):
        mock_requests.Session.return_value = mock_session
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--image", "image1.png", "--status", "async"],
        )

    assert result.exit_code == 0
    mock_session.get.assert_called_once_with("https://example/api/v1/media/mid1")
    mock_time.sleep.assert_called_once_with(1)

    status_call = mock_session.post.call_args_list[1]
    assert status_call[1]["json"]["media_ids"] == ["mid1"]


def test_post_media_unknown_target():
    """--target with invalid value should fail."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config", "config.json", "--status", "hello", "--target", "twitter"],
    )
    assert result.exit_code != 0


def test_bluesky_text_only():
    """Post text to Bluesky without images."""
    mock_session = MagicMock()
    # createSession response
    mock_session.post.side_effect = [
        MagicMock(status_code=200, json=lambda: {
            "did": "did:plc:1234",
            "accessJwt": "jwt-token",
        }),
        # createRecord response
        MagicMock(status_code=200, json=lambda: {
            "uri": "at://did:plc:1234/app.bsky.feed.post/abc",
            "cid": "bafyabc",
        }),
    ]

    config_json = '{"bluesky_handle":"test.bsky.social","bluesky_password":"app-pass"}'
    open_mock = _mock_open(config_json, {})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock):
        mock_requests.Session.return_value = mock_session
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--status", "hello bluesky", "--target", "bluesky"],
        )

    assert result.exit_code == 0

    # Verify createSession call
    auth_call = mock_session.post.call_args_list[0]
    assert "com.atproto.server.createSession" in auth_call[0][0]
    assert auth_call[1]["json"]["identifier"] == "test.bsky.social"

    # Verify createRecord call
    record_call = mock_session.post.call_args_list[1]
    assert "com.atproto.repo.createRecord" in record_call[0][0]
    payload = record_call[1]["json"]
    assert payload["repo"] == "did:plc:1234"
    assert payload["collection"] == "app.bsky.feed.post"
    assert payload["record"]["text"] == "hello bluesky"
    assert payload["record"]["$type"] == "app.bsky.feed.post"


def test_bluesky_with_images():
    """Post to Bluesky with images and alt text."""
    img1 = BytesIO(b"data1")
    img2 = BytesIO(b"data2")

    mock_session = MagicMock()
    mock_session.post.side_effect = [
        # createSession
        MagicMock(status_code=200, json=lambda: {
            "did": "did:plc:1234",
            "accessJwt": "jwt-token",
        }),
        # uploadBlob 1
        MagicMock(status_code=200, json=lambda: {
            "blob": {"$type": "blob", "ref": {"$link": "bafyimg1"}, "mimeType": "image/png", "size": 5},
        }),
        # uploadBlob 2
        MagicMock(status_code=200, json=lambda: {
            "blob": {"$type": "blob", "ref": {"$link": "bafyimg2"}, "mimeType": "image/png", "size": 5},
        }),
        # createRecord
        MagicMock(status_code=200, json=lambda: {
            "uri": "at://did:plc:1234/app.bsky.feed.post/abc",
            "cid": "bafyabc",
        }),
    ]

    config_json = '{"bluesky_handle":"test.bsky.social","bluesky_password":"app-pass"}'
    open_mock = _mock_open(config_json, {"img1.png": img1, "img2.png": img2})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock):
        mock_requests.Session.return_value = mock_session
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--image", "img1.png,img2.png",
             "--alt", "first,second", "--status", "pics", "--target", "bluesky"],
        )

    assert result.exit_code == 0

    # Verify blob uploads
    upload1 = mock_session.post.call_args_list[1]
    assert "com.atproto.repo.uploadBlob" in upload1[0][0]

    # Verify record has embed with images
    record_call = mock_session.post.call_args_list[3]
    payload = record_call[1]["json"]
    embed = payload["record"]["embed"]
    assert embed["$type"] == "app.bsky.embed.images"
    assert len(embed["images"]) == 2
    assert embed["images"][0]["alt"] == "first"
    assert embed["images"][1]["alt"] == "second"


def test_bluesky_missing_credentials():
    """Bluesky target with missing credentials should fail gracefully."""
    config_json = '{"mastodon_token":"token"}'
    open_mock = _mock_open(config_json, {})

    with patch("builtins.open", open_mock):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--status", "hello", "--target", "bluesky"],
        )

    assert result.exit_code == 0  # graceful exit, not crash


def test_bluesky_text_too_long():
    """Bluesky rejects text over 300 characters before making any network calls."""
    config_json = '{"bluesky_handle":"test.bsky.social","bluesky_password":"app-pass"}'
    open_mock = _mock_open(config_json, {})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--status", "x" * 301, "--target", "bluesky"],
        )

    assert result.exit_code == 1
    mock_requests.Session.return_value.post.assert_not_called()


def test_bluesky_too_many_images():
    """Bluesky rejects more than 4 images before making any network calls."""
    config_json = '{"bluesky_handle":"test.bsky.social","bluesky_password":"app-pass"}'
    open_mock = _mock_open(config_json, {})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--image", "a.png,b.png,c.png,d.png,e.png",
             "--status", "too many", "--target", "bluesky"],
        )

    assert result.exit_code == 1
    mock_requests.Session.return_value.post.assert_not_called()


def test_bluesky_warns_on_mastodon_flags():
    """Bluesky target warns when Mastodon-only flags are used."""
    mock_session = MagicMock()
    mock_session.post.side_effect = [
        MagicMock(status_code=200, json=lambda: {
            "did": "did:plc:1234",
            "accessJwt": "jwt-token",
        }),
        MagicMock(status_code=200, json=lambda: {
            "uri": "at://did:plc:1234/app.bsky.feed.post/abc",
            "cid": "bafyabc",
        }),
    ]

    config_json = '{"bluesky_handle":"test.bsky.social","bluesky_password":"app-pass"}'
    open_mock = _mock_open(config_json, {})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock), \
         patch("comrade.scripts.post_media.logger") as mock_logger:
        mock_requests.Session.return_value = mock_session
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--status", "hello", "--target", "bluesky",
             "--sensitive", "--cw", "spoiler"],
        )

    assert result.exit_code == 0
    warning_calls = mock_logger.warning.call_args_list
    assert len(warning_calls) > 0
    warning_message = str(warning_calls[0])
    assert "sensitive" in warning_message or "cw" in warning_message


def test_bluesky_timestamp_format():
    """Bluesky createdAt should use Z suffix."""
    mock_session = MagicMock()
    mock_session.post.side_effect = [
        MagicMock(status_code=200, json=lambda: {
            "did": "did:plc:1234",
            "accessJwt": "jwt-token",
        }),
        MagicMock(status_code=200, json=lambda: {
            "uri": "at://did:plc:1234/app.bsky.feed.post/abc",
            "cid": "bafyabc",
        }),
    ]

    config_json = '{"bluesky_handle":"test.bsky.social","bluesky_password":"app-pass"}'
    open_mock = _mock_open(config_json, {})

    with patch("comrade.scripts.post_media.requests") as mock_requests, \
         patch("builtins.open", open_mock):
        mock_requests.Session.return_value = mock_session
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--config", "config.json", "--status", "hello", "--target", "bluesky"],
        )

    record_call = mock_session.post.call_args_list[1]
    created_at = record_call[1]["json"]["record"]["createdAt"]
    assert created_at.endswith("Z")
    assert "+00:00" not in created_at
