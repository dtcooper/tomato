from collections import namedtuple
import datetime
import json
import logging
import math
import subprocess

from constance import config


logger = logging.getLogger(__name__)
FFProbe = namedtuple("FFProbe", ("format", "duration", "title"))


FILE_FORMATS = {
    "mp3": {"format": "mp3", "ext": "mp3", "encode_args": ("-ac", "2", "-a:b", "192k")},
    "ogg/vorbis (128kbit)": {"format": "flac", "ext": "flac"},
    "ogg (192kpbs)": {"format": "ogg", "ext": "mp3", "encode_args": ("-ac", "2", "-a:b", "192k")},
}


def ffprobe(infile):
    # We want at least one audio channel
    cmd = subprocess.run(
        (
            "ffprobe",
            "-i",
            infile,
            "-print_format",
            "json",
            "-hide_banner",
            "-loglevel",
            "error",
            "-show_format",
            "-show_error",
            "-show_streams",
            "-select_streams",
            "a:0",
        ),
        text=True,
        capture_output=True,
    )

    kwargs = {}
    if cmd.returncode == 0:
        data = json.loads(cmd.stdout)
        if data and data["streams"] and data["format"]:
            kwargs.update(
                {
                    "format": data["format"]["format_name"],
                    "duration": datetime.timedelta(seconds=math.ceil(float(data["streams"][0].get("duration") or 0))),
                }
            )
        else:
            logger.warning(f"ffprobe returned a bad or empty response: {cmd.stdout}")
            return None
    else:
        logger.warning(f"ffprobe returned {cmd.returncode}: {cmd.stderr}")
        return None

    tags = data["format"].get("tags", {})
    tags = [tags.get(field, "").strip() for field in ("artist", "title")]
    title = (" - ".join(tag for tag in tags if tag)).strip() or None
    return FFProbe(title=title, **kwargs)


def ffmpeg_convert(infile, outfile):
    if not outfile.name.lower().endswith(".mp3"):
        raise Exception("Will only convert to MP3")

    args = [
        "ffmpeg",
        "-y",
        "-i",
        infile,
        "-hide_banner",
        "-loglevel",
        "error",
        "-map",
        "0:a:0",
        "-b:a",
        f"{config.AUDIO_BITRATE}k",
    ]

    if config.TRIM_SILENCE:
        threshold = f"{config.TRIM_SILENCE_LESS_THAN_DECIBELS}"
        args.extend(
            [
                "-af",
                (
                    f"silenceremove=start_periods=1:start_duration=0.25:start_threshold={threshold}dB:"
                    f"stop_periods=1:stop_duration=0.25:stop_threshold={threshold}dB"
                ),
            ]
        )
    args.append(outfile)

    cmd = subprocess.run(args, text=True, capture_output=True)
    if cmd.returncode != 0:
        logger.error(f"ffmpeg returned {cmd.returncode}: {cmd.stderr}")

    return cmd.returncode == 0
