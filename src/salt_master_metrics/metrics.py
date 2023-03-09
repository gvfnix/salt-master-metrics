import prometheus_client
import datetime
import salt_master_metrics.global_logger


log = salt_master_metrics.global_logger.getLogger(__name__)


minions_pending = {}
minions_ping = {}


prometheus_metrics = {
    "new_jobs": prometheus_client.Counter(
        "salt_new_jobs",
        "Total quantity of new jobs",
        ["fun"]
    ),
    "minion`_failed_job": prometheus_client.Counter(
        "salt_minion_failed_job",
        "Failed job events",
        ["minion", "fun", "jid"]
    ),
    "minions_connected": prometheus_client.Gauge(
        "salt_minions_connected",
        "Quantity of currently connected minions"
    ),
    "minions_pending": prometheus_client.Gauge(
        "salt_minions_pending_auth",
        "Quantity of minions pending auth"
    )
}


def register_new_job(event, counter):
    if event["tag"].endswith("/new"):
        labels = {"fun": event["data"].get("fun", "")}
        counter.labels(**labels).inc()
        log.debug(f"Register new job with labels {labels}")


def register_failed_job(event, counter):
    if "/ret/" not in event["tag"]:
        return
    data = event["data"]
    success = data["success"]
    if success:
        return
    labels = {
        "minion": data.get("id", ""),
        "fun": data.get("fun", ""),
        "jid": data.get("jid", "")
    }
    counter.labels(**labels).inc()
    log.debug(f"Register minion job failure with labels {labels}")


def register_connected_minions(event, gauge, threshold:datetime.datetime=datetime.datetime.now()):
    if event["tag"] == "salt/presence/present":
        present_minions = event["data"].get("present", [])
        recent_pinged_minions = filter(
            lambda item: threshold - item[1] < datetime.timedelta(seconds=90),
            minions_ping.items()
        )
        gauge_value = len(present_minions) + len(dict(recent_pinged_minions))
        gauge.set(gauge_value)
    if event["tag"] == "minion_ping":
        minion_id = event["data"]["id"]
        minions_ping[minion_id] = datetime.datetime.now()


def register_pending_minions(event, gauge):
    if event["tag"] != "salt/auth":
        return
    data = event["data"]
    minion_id = data.get("id", "")
    action = data.get("act", "")
    if action == "pend":
        minions_pending[minion_id] = 1
        log.debug(f"Added {minion_id} as pending")
    elif action == "accept"and minion_id in minions_pending:
        del minions_pending[minion_id]
        log.debug(f"Removed {minion_id} from pending")
    gauge.set(len(minions_pending))


registrators = {
    "new_jobs": register_new_job,
    "minion_failed_job": register_failed_job,
    "minions_connected": register_connected_minions,
    "minions_pending": register_pending_minions,
}


def register_event(event, metrics=prometheus_metrics):
    log.debug(f"Got event: {event}")
    if type(event) is not dict:
        log.debug("Event is not a dict, skipping")
        return
    if "tag" not in event:
        log.debug("Event has no tag, skipping")
        return
    if "data" not in event:
        log.debug("Event has no data, skipping")
        return
    for registrator_key in registrators.keys():
        registrator = registrators[registrator_key]
        metric = metrics[registrator_key]
        registrator(event, metric)


