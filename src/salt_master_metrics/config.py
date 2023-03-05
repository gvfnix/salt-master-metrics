import environ

@environ.config(prefix="SALT_MASTER_METRICS")
class AppConfig(object):
    master_config_file = environ.var("/etc/salt/master")
    listen_port = environ.var(2112, converter=int)
    log_level = environ.var("INFO")


def get_config():
    config = AppConfig.from_environ()
    return config
