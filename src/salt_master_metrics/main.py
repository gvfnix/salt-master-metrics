import salt_master_metrics.global_logger
import salt_master_metrics.config
import salt_master_metrics.metrics
import salt_master_metrics.event_listener
import prometheus_client


def ioloop(listener):
    for event in listener.iter_events(full=True):
        salt_master_metrics.metrics.register_event(event)


def run():
    log = salt_master_metrics.global_logger.getLogger(__name__)
    config = salt_master_metrics.config.get_config()
    log.info("Start")
    prometheus_client.start_http_server(config.listen_port)
    listener = salt_master_metrics.event_listener.connect(config)
    ioloop(listener)
    return 0
