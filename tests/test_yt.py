from argparse import Namespace

import pytest

from cases.webs import yt


def make_args(**overrides):
    defaults = dict(
        urls=["https://youtube.com/watch?v=abc"],
        audio=False,
        playlist=False,
        transcript_langs=None,
        cloud=False,
        browser="chrome",
    )
    defaults.update(overrides)
    return Namespace(**defaults)


def make_fake_ydl_class(url_to_finished_paths):
    """Fake yt_dlp.YoutubeDL - records the opts it's constructed with, and
    on download() fires the configured progress_hooks with "finished"
    events for whatever paths the test wants that URL to have produced,
    creating the file for real so glob-based logic (the audio move) has
    something to find."""

    class FakeYoutubeDL:
        instances = []

        def __init__(self, opts):
            self.opts = opts
            type(self).instances.append(self)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def download(self, urls):
            for url in urls:
                for finished_path in url_to_finished_paths.get(url, []):
                    finished_path.parent.mkdir(parents=True, exist_ok=True)
                    if not finished_path.exists():
                        finished_path.write_bytes(b"fake")
                    for hook in self.opts.get("progress_hooks", []):
                        hook({"status": "finished", "filename": str(finished_path)})

    return FakeYoutubeDL


# --- build_ydl_opts ---


def test_build_ydl_opts_single_video_nests_under_its_own_title_subfolder(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(), progress_hook=lambda d: None)

    assert opts["outtmpl"] == str(tmp_path / "%(title)q" / "%(title)q.%(ext)s")
    assert opts["noplaylist"] is True


def test_build_ydl_opts_playlist_nests_under_playlist_title(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(playlist=True), progress_hook=lambda d: None)

    assert opts["outtmpl"] == str(tmp_path / "%(playlist_title,playlist)q" / "%(playlist_index)s - %(title)q.%(ext)s")
    assert opts["noplaylist"] is False


def test_build_ydl_opts_audio_sets_postprocessor_and_keeps_video(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(audio=True), progress_hook=lambda d: None)

    assert opts["postprocessors"] == [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
    assert opts["keepvideo"] is True


def test_build_ydl_opts_without_audio_has_no_postprocessors(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(), progress_hook=lambda d: None)

    assert "postprocessors" not in opts
    assert "keepvideo" not in opts


def test_build_ydl_opts_transcript_langs_sets_subtitle_options(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(transcript_langs=["en", "sk"]), progress_hook=lambda d: None)

    assert opts["writesubtitles"] is True
    assert opts["writeautomaticsub"] is True
    assert opts["subtitleslangs"] == ["en", "sk"]
    assert opts["subtitlesformat"] == "srt"


def test_build_ydl_opts_without_transcript_langs_skips_subtitle_options(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(), progress_hook=lambda d: None)

    assert "writesubtitles" not in opts
    assert "subtitleslangs" not in opts


def test_build_ydl_opts_browser_sets_cookie_options(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(browser="edge"), progress_hook=lambda d: None)

    assert opts["cookiesfrombrowser"] == ("edge",)


def test_build_ydl_opts_no_browser_skips_cookie_options(tmp_path):
    opts = yt.build_ydl_opts(tmp_path, make_args(browser=None), progress_hook=lambda d: None)

    assert "cookiesfrombrowser" not in opts


# --- download_one ---


def test_download_one_returns_content_folder_from_finished_file(tmp_path, monkeypatch):
    url = "https://youtube.com/watch?v=abc"
    video_path = tmp_path / "output" / "My Video" / "My Video.mp4"
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": make_fake_ydl_class({url: [video_path]})}))

    content_folder = yt.download_one(url, tmp_path / "output", make_args(urls=[url]))

    assert content_folder == video_path.parent
    assert video_path.is_file()


def test_download_one_returns_none_when_nothing_finished(tmp_path, monkeypatch):
    url = "https://youtube.com/watch?v=abc"
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": make_fake_ydl_class({})}))

    content_folder = yt.download_one(url, tmp_path / "output", make_args(urls=[url]))

    assert content_folder is None


# --- move_audio_files ---


def test_move_audio_files_moves_mp3_into_audio_subfolder(tmp_path):
    content_folder = tmp_path / "My Video"
    content_folder.mkdir()
    mp3_path = content_folder / "My Video.mp3"
    mp3_path.write_bytes(b"fake-audio")

    moved = yt.move_audio_files(content_folder)

    destination = content_folder / "audio" / "My Video.mp3"
    assert moved == [destination]
    assert destination.is_file()
    assert not mp3_path.exists()


def test_move_audio_files_leaves_video_file_alone(tmp_path):
    content_folder = tmp_path / "My Video"
    content_folder.mkdir()
    video_path = content_folder / "My Video.mp4"
    video_path.write_bytes(b"fake-video")

    moved = yt.move_audio_files(content_folder)

    assert moved == []
    assert video_path.is_file()
    assert not (content_folder / "audio").exists()


# --- move_to_cloud ---


def test_move_to_cloud_moves_folder_under_given_subfolder(tmp_path):
    content_folder = tmp_path / "output" / "My Video"
    content_folder.mkdir(parents=True)
    (content_folder / "My Video.mp4").write_bytes(b"fake-video")
    cloud_root = tmp_path / "CloudDrive"
    cloud_root.mkdir()

    destination = yt.move_to_cloud(content_folder, cloud_root, "output")

    assert destination == cloud_root / "output" / "My Video"
    assert (destination / "My Video.mp4").is_file()
    assert not content_folder.exists()


def test_move_to_cloud_respects_a_custom_output_subfolder_name(tmp_path):
    content_folder = tmp_path / "output" / "My Video"
    content_folder.mkdir(parents=True)
    cloud_root = tmp_path / "CloudDrive"
    cloud_root.mkdir()

    destination = yt.move_to_cloud(content_folder, cloud_root, "custom-output")

    assert destination == cloud_root / "custom-output" / "My Video"


# --- main ---


def test_main_downloads_into_default_output_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)
    url = "https://youtube.com/watch?v=abc"
    video_path = tmp_path / ".boring-stuff" / "output" / "My Video" / "My Video.mp4"
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": make_fake_ydl_class({url: [video_path]})}))

    yt.main([url])

    assert video_path.is_file()


def test_main_audio_flag_moves_mp3_into_audio_subfolder(tmp_path, monkeypatch):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)
    url = "https://youtube.com/watch?v=abc"
    content_folder = tmp_path / ".boring-stuff" / "output" / "My Video"
    video_path = content_folder / "My Video.mp4"
    mp3_path = content_folder / "My Video.mp3"
    fake_class = make_fake_ydl_class({url: [video_path, mp3_path]})
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": fake_class}))

    yt.main(["-a", url])

    assert video_path.is_file()
    assert (content_folder / "audio" / "My Video.mp3").is_file()
    assert not mp3_path.exists()
    assert fake_class.instances[0].opts["keepvideo"] is True


def test_main_transcript_flags_are_repeatable_and_collected(tmp_path, monkeypatch):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)
    url = "https://youtube.com/watch?v=abc"
    video_path = tmp_path / ".boring-stuff" / "output" / "My Video" / "My Video.mp4"
    fake_class = make_fake_ydl_class({url: [video_path]})
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": fake_class}))

    yt.main(["-ten", "-tsk", url])

    assert fake_class.instances[0].opts["subtitleslangs"] == ["en", "sk"]


def test_main_processes_multiple_urls_each_with_their_own_content_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)
    url_a = "https://youtube.com/watch?v=aaa"
    url_b = "https://youtube.com/watch?v=bbb"
    path_a = tmp_path / ".boring-stuff" / "output" / "Video A" / "Video A.mp4"
    path_b = tmp_path / ".boring-stuff" / "output" / "Video B" / "Video B.mp4"
    fake_class = make_fake_ydl_class({url_a: [path_a], url_b: [path_b]})
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": fake_class}))

    yt.main([url_a, url_b])

    assert path_a.is_file()
    assert path_b.is_file()
    # each URL got its own YoutubeDL.download([url]) call, not a batched one
    assert len(fake_class.instances) == 2


def test_main_prints_message_and_continues_when_nothing_downloaded(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)
    url = "https://youtube.com/watch?v=abc"
    fake_class = make_fake_ydl_class({})
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": fake_class}))

    yt.main([url])  # must not raise

    assert f"Nothing was downloaded for {url}" in capsys.readouterr().out


def test_main_cloud_flag_prompts_for_config_and_moves_content_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)
    cloud_root = tmp_path / "CloudDrive"
    cloud_root.mkdir()
    url = "https://youtube.com/watch?v=abc"
    video_path = tmp_path / ".boring-stuff" / "output" / "My Video" / "My Video.mp4"
    monkeypatch.setattr(yt, "yt_dlp", type("m", (), {"YoutubeDL": make_fake_ydl_class({url: [video_path]})}))

    folder_calls = []
    subfolder_calls = []
    monkeypatch.setattr(yt, "load_cloud_folder", lambda: folder_calls.append(True) or cloud_root)
    monkeypatch.setattr(
        yt, "load_cloud_subfolder_name", lambda key, default: subfolder_calls.append((key, default)) or default
    )

    yt.main(["-c", url])

    assert folder_calls == [True]
    assert subfolder_calls == [("output", "output")]
    assert (cloud_root / "output" / "My Video" / "My Video.mp4").is_file()
    assert not video_path.parent.exists()


def test_main_cloud_exits_cleanly_when_config_cannot_be_obtained(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)

    def raise_missing():
        raise yt.MissingConfigError("Cloud folder root is not configured, and no terminal is attached.")

    monkeypatch.setattr(yt, "load_cloud_folder", raise_missing)

    with pytest.raises(SystemExit):
        yt.main(["-c", "https://youtube.com/watch?v=abc"])

    assert "not configured" in capsys.readouterr().out


def test_main_cloud_exits_cleanly_when_configured_folder_not_accessible(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(yt.Path, "home", lambda: tmp_path)
    missing = tmp_path / "not-mounted"
    monkeypatch.setattr(yt, "load_cloud_folder", lambda: missing)
    monkeypatch.setattr(yt, "load_cloud_subfolder_name", lambda key, default: default)

    with pytest.raises(SystemExit):
        yt.main(["-c", "https://youtube.com/watch?v=abc"])

    assert "not accessible" in capsys.readouterr().out
