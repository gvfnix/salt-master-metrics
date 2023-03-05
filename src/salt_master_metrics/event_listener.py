import salt.utils.event
import salt.config
from salt_master_metrics.config import AppConfig

def connect(config: AppConfig) -> salt.utils.event.MasterEvent:
    conf_file = config.master_config_file
    master_opts = salt.config.client_config(conf_file)
    listener = salt.utils.event.get_event(
        "master",
        master_opts["sock_dir"],
        master_opts["transport"],
        opts=master_opts,
        listen=True
    )
    return listener
