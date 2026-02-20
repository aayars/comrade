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
