from io import BytesIO, StringIO
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

from comrade.scripts.post_media import main


def _mock_open(config_json, files):
    real_open = open

    def side_effect(path, mode="r", *args, **kwargs):
        if path in files:
            return files[path]
        return real_open(path, mode, *args, **kwargs)

    mock = Mock(side_effect=side_effect)

    # config.json needs to work with json.load
    files.setdefault("config.json", StringIO(config_json))

    return mock


def test_post_media_multiple_images():
    config_json = '{"mastodon_token":"token","mastodon_instance":"https://example"}'
    img1 = BytesIO(b"data1")
    img2 = BytesIO(b"data2")

    mock_session = MagicMock()
    mock_session.post.side_effect = [
        # Two media uploads (v2/media returns 200 = done)
        MagicMock(status_code=200, json=lambda: {"id": "mid1"}),
        MagicMock(status_code=200, json=lambda: {"id": "mid2"}),
        # Status post
        MagicMock(status_code=200),
    ]

    open_mock = _mock_open(config_json, {"image1.png": img1, "image2.png": img2})

    with patch("comrade.scripts.post_media.requests") as mock_requests:
        mock_requests.Session.return_value = mock_session
        with patch("builtins.open", open_mock):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--config", "config.json", "--image", "image1.png,image2.png", "--status", "hello"],
            )

    assert result.exit_code == 0

    # Two media uploads + one status post
    assert mock_session.post.call_count == 3

    # Verify status post payload
    status_call = mock_session.post.call_args_list[2]
    assert status_call[0][0] == "https://example/api/v1/statuses"
    assert status_call[1]["json"]["status"] == "hello"
    assert status_call[1]["json"]["media_ids"] == ["mid1", "mid2"]


def test_post_media_no_image():
    config_json = '{"mastodon_token":"token","mastodon_instance":"https://example"}'

    mock_session = MagicMock()
    mock_session.post.return_value = MagicMock(status_code=200)

    open_mock = _mock_open(config_json, {})

    with patch("comrade.scripts.post_media.requests") as mock_requests:
        mock_requests.Session.return_value = mock_session
        with patch("builtins.open", open_mock):
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
