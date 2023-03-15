import environ
from datetime import timedelta


def tointerval(s: str) -> timedelta:
    units = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }
    unitletter = s[-1]
    if unitletter not in units:
        raise ValueError(f"Interval units must be one of {list(units.keys())}")
    interval_length = s[:-1]
    if not interval_length.isdigit:
        raise ValueError("Interval length must be a natural number")
    return timedelta(seconds=int(interval_length)*units[unitletter])


@environ.config(prefix="SALT_MASTER_METRICS")
class AppConfig(object):
    master_config_file = environ.var("/etc/salt/master")
    listen_port = environ.var(2112, converter=int)
    log_level = environ.var("INFO")
    minion_ping_timeout = environ.var("90s", converter=tointerval)
    failure_event_retention_interval = environ.var("1d", converter=tointerval)


def get_config():
    config = AppConfig.from_environ()
    return config
