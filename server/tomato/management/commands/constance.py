from constance.management.commands.constance import Command as ConstanceCommand

from ...utils import send_config_update_redis_message


class Command(ConstanceCommand):
    def handle(self, *args, **kwargs):
        try:
            super().handle(*args, **kwargs)
        finally:
            send_config_update_redis_message()
