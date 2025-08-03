import json
import builtins
import sys
import types
from pathlib import Path

from click.testing import CliRunner


class _DummyLogger:
    def add(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


def test_files_closed_after_run(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    # Stub optional dependencies before importing the module under test.
    monkeypatch.setitem(sys.modules, "loguru", types.SimpleNamespace(logger=_DummyLogger()))
    monkeypatch.setitem(sys.modules, "mastodon", types.SimpleNamespace(Mastodon=object))

    from comrade.scripts import post_media
    from comrade.scripts.post_media import main

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"mastodon_token": "t", "mastodon_instance": "https://example.com"})
    )
    image_file = tmp_path / "image.txt"
    image_file.write_text("data")

    close_counts = {"config": 0, "image": 0}
    orig_open = builtins.open

    def tracking_open(path, *args, **kwargs):
        f = orig_open(path, *args, **kwargs)
        tag = None
        if path == str(config_file):
            tag = "config"
        elif path == str(image_file):
            tag = "image"
        if tag:
            orig_close = f.close

            def close():
                close_counts[tag] += 1
                return orig_close()

            f.close = close
        return f

    monkeypatch.setattr(builtins, "open", tracking_open)

    class DummyMastodon:
        def __init__(self, *args, **kwargs):
            pass

        def media_post(self, fileobj, mime_type, description=None, synchronous=False):
            assert not fileobj.closed
            return {"id": "1"}

        def status_post(self, *args, **kwargs):
            return {}

    monkeypatch.setattr(post_media, "Mastodon", DummyMastodon)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config", str(config_file), "--image", str(image_file), "--status", "hello"],
    )
    assert result.exit_code == 0, result.output
    assert close_counts["config"] == 1
    assert close_counts["image"] == 1
