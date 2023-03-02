import salt.utils.event
import salt.config
import logging


def connect(config: dict) -> salt.utils.event.MasterEvent:
    log = logging.getLogger(__name__)
    conf_file = config["master_config_file"]
    master_opts = salt.config.master_config(conf_file)
    listener = salt.utils.event.get_master_event(
        master_opts,
        master_opts["sock_dir"]
    )
    log.info("Connected to event bus")
    return listener
