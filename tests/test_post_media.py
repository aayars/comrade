import os
import sys
import types
from io import BytesIO, StringIO
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_post_media_multiple_images():
    mastodon_instance = MagicMock()
    mastodon_module = types.SimpleNamespace(
        Mastodon=MagicMock(return_value=mastodon_instance)
    )
    logger_module = types.SimpleNamespace(logger=MagicMock())

    config_path = "config.json"
    image1 = "image1.png"
    image2 = "image2.png"
    config_json = (
        '{"mastodon_token":"token","mastodon_instance":"https://example"}'
    )
    img_file1 = BytesIO(b"data1")
    img_file2 = BytesIO(b"data2")

    real_open = open

    def open_side_effect(path, mode='r', *args, **kwargs):
        if path == config_path:
            return StringIO(config_json)
        elif path == image1:
            return img_file1
        elif path == image2:
            return img_file2
        return real_open(path, mode, *args, **kwargs)

    open_mock = Mock(side_effect=open_side_effect)

    with patch.dict(sys.modules, {"mastodon": mastodon_module, "loguru": logger_module}):
        from comrade.scripts import post_media
        runner = CliRunner()
        with patch("builtins.open", open_mock):
            mastodon_instance.media_post.side_effect = [
                {"id": "mid1"},
                {"id": "mid2"},
            ]
            result = runner.invoke(
                post_media.main,
                [
                    "--config",
                    config_path,
                    "--image",
                    image1,
                    "--image",
                    image2,
                    "--status",
                    "hello",
                ],
            )

    assert result.exit_code == 0
    assert mastodon_instance.media_post.call_count == 2
    assert mastodon_instance.media_post.call_args_list[0][0][0] is img_file1
    assert mastodon_instance.media_post.call_args_list[1][0][0] is img_file2
    mastodon_instance.status_post.assert_called_once_with(
        "hello",
        in_reply_to_id=None,
        media_ids=["mid1", "mid2"],
        sensitive=False,
        visibility="public",
        spoiler_text=None,
    )
