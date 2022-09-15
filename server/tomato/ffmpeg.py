from collections import namedtuple
import datetime
import json
import logging
import math
import subprocess


logger = logging.getLogger(__name__)
FFProbe = namedtuple("FFProbe", ("format", "duration", "title"))


def ffprobe(url):
    # We want at least one audio channel
    cmd = subprocess.run(
        [
            "ffprobe",
            "-i",
            url,
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
        ],
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
