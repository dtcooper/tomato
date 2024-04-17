import json
import os
from pathlib import Path

from django.core.serializers.json import DjangoJSONEncoder


def once_at_startup(crontab):
    needs_to_run = True

    def startup_crontab(*args, **kwargs):
        nonlocal needs_to_run
        if needs_to_run:
            needs_to_run = False
            return True
        else:
            return crontab(*args, **kwargs)

    return startup_crontab


def django_json_dumps(obj):
    return json.dumps(obj, separators=(",", ":"), cls=DjangoJSONEncoder)


def listdir_recursive(dirname):
    dirname = Path(dirname)
    files = (os.path.join(dp, f) for dp, _, fn in os.walk(dirname) for f in fn)
    return [str(Path(file).relative_to(dirname)) for file in files]
