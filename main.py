import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger(__name__)

import prometheus_client
import metrics
import event_listener
import os


def get_config():
    config = {
        "listen_port": 2112,
        "master_config_file": "/etc/salt/master"
    }
    listen_port = os.environ.get(
        "SALT_MASTER_METRICS_LISTEN_PORT",
        str(config["listen_port"])
    )
    config["master_config_file"] = os.environ.get(
        "SALT_MASTER_METRICS_MASTER_CONFIG_FILE",
        config["master_config_file"]
    )
    if listen_port.isdigit() :
        config["listen_port"] = int(listen_port)
    return config

def main(config: dict):
    prometheus_client.start_http_server(config["listen_port"])
    listener = event_listener.connect(config)
    while True:
        event = listener.get_event(wait=5)
        metrics.register_event(event)

if __name__ == "__main__":
    config = get_config()
    main(config)