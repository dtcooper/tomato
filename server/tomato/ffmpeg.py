from collections import namedtuple
import datetime
import json
import logging
import math
import shlex
import subprocess

from constance import config


logger = logging.getLogger(__name__)
FFProbe = namedtuple("FFProbe", ("format", "duration", "title"))


def run_command(args):
    logger.info(f"Executing: {shlex.join(map(str, args))}")
    return subprocess.run(args, text=True, capture_output=True)


def ffprobe(infile):
    # We want at least one audio channel
    cmd = run_command(
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
        )
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
    # May create multiple files in outfile' directory, so it should be removed

    if not outfile.name.lower().endswith(".mp3"):
        raise Exception("Will only convert to MP3")

    ARGS_INFILE_INDEX = 3
    base_args = [
        "ffmpeg",
        "-y",
        "-i",
        infile,
    ]
    ARGS_INFILE_INDEX = len(base_args) - 1  # used below
    base_args.extend(
        [
            "-hide_banner",
            "-loglevel",
            "error",
            "-id3v2_version",
            "3",
            "-map",
            "0:a:0",
        ]
    )

    if config.TRIM_SILENCE:
        trimmed_wav_file = outfile.with_suffix(".wav")
        untrimmed_wav_file = trimmed_wav_file.with_stem(f"{outfile.stem}-untrimmed")

        args = base_args + [untrimmed_wav_file]
        cmd = run_command(args)
        if cmd.returncode != 0:
            logger.error(f"ffmpeg (trim) returned {cmd.returncode}: {cmd.stderr}")
            return False

        args = (
            "sox",
            untrimmed_wav_file,
            trimmed_wav_file,
            "silence",
            "1",
            "0.1",
            "0.1%",
            "reverse",
            "silence",
            "1",
            "0.1",
            "0.1%",
            "reverse",
        )
        cmd = run_command(args)
        if cmd.returncode != 0:
            logger.error(f"sox returned {cmd.returncode}: {cmd.stderr}")
            return False

        untrimmed_wav_file.unlink(missing_ok=True)
        base_args[ARGS_INFILE_INDEX] = trimmed_wav_file  # Swap out trimmed file

    args = base_args + ["-b:a", f"{config.AUDIO_BITRATE}k", outfile]
    cmd = run_command(args)
    if cmd.returncode != 0:
        logger.error(f"ffmpeg (final) returned {cmd.returncode}: {cmd.stderr}")

    if config.TRIM_SILENCE:
        trimmed_wav_file.unlink(missing_ok=True)

    return cmd.returncode == 0
