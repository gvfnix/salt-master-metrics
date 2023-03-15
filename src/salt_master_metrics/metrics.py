import prometheus_client
import datetime
from salt_master_metrics import global_logger, config
import json


log = global_logger.getLogger(__name__)
conf = config.get_config()

salt_master_minions_count = prometheus_client.Gauge(
    "salt_master_minions_count",
    "Quantity of minions",
    ["state"]
)
salt_master_function_call_count = prometheus_client.Counter(
    "salt_master_function_call_count",
    "How many times the function was called",
    ["fun"]
)
salt_master_job_failed = prometheus_client.Counter(
    "salt_master_job_failed",
    "Registered job failure",
    ['comment', 'fun', 'jid', 'minion', 'name', 'sls']
)
__minions_pending = {}
__minions_ping = {}
__failures = {}


def clear():
    __minions_pending = {}
    __minions_ping = {}
    salt_master_minions_count.clear()
    salt_master_function_call_count.clear()
    salt_master_job_failed.clear()


def register_function_call(data):
    fun = data.get("fun", "")
    salt_master_function_call_count.labels(fun=fun).inc()


def older_than(timestamp: datetime.datetime, interval: datetime.timedelta) -> bool:
    now = datetime.datetime.now()
    timediff = now - timestamp
    return timediff > interval


def clear_old(_dict: dict, threshold: datetime.timedelta):
    recents = {
        key: timestamp for key, timestamp in _dict.items()
        if not older_than(timestamp, threshold)
    }
    _dict.clear()
    _dict.update(recents)


def __cleanup_old_failures():
    threshold = conf.failure_event_retention_interval
    for labels_json, create_time in __failures.items():
        if older_than(create_time, threshold):
            labels = json.loads(labels_json)
            label_values_sorted_by_key = [
                item[1] for item in sorted(labels.items())
            ]
            salt_master_job_failed.remove(*label_values_sorted_by_key)
    clear_old(__failures, threshold)


def __register_failure_with_datetime(labels: dict):
    __cleanup_old_failures()
    salt_master_job_failed.labels(**labels).inc()
    log.debug(f"Register minion job failure with labels {labels}")
    labels_json = json.dumps(labels)
    now = datetime.datetime.now()
    __failures[labels_json] = now


def register_failed_job(data):
    labels = {
        "minion": data.get("id", ""),
        "fun": data.get("fun", ""),
        "jid": data.get("jid", ""),
        "name": "",
        "comment": "",
        "sls": "",
    }
    _return = data.get("return", {})
    if type(_return) is dict:
        for k, _ret_data in _return.items():
            result = _ret_data.get("result", True)
            if not result:
                labels["name"] = _ret_data.get("__id__", "")
                labels["comment"] = _ret_data.get("comment", "")
                labels["sls"] = _ret_data.get("__sls__", "")
                __register_failure_with_datetime(labels)
    elif type(_return) is list:
        for comment in _return:
            labels["comment"] = comment
            __register_failure_with_datetime(labels)
    elif type(_return) is str:
        labels["comment"] = _return
        __register_failure_with_datetime(labels)


def register_presence(data: dict):
    present_minions = data.get("present", [])
    now = datetime.datetime.now()
    threshold = conf.minion_ping_timeout
    clear_old(__minions_ping, threshold)
    clear_old(__minions_pending, threshold)
    _value = len(present_minions) + len(__minions_ping)
    salt_master_minions_count.labels(
        state="connected"
    ).set(_value)
    salt_master_minions_count.labels(
        state="pending"
    ).set(len(__minions_pending))


def register_ping(data: dict):
    now = datetime.datetime.now()
    minion_id = data.get("id", "__none__")
    __minions_ping[minion_id] = now


def register_authorization(data):
    minion_id = data.get("id", "")
    action = data.get("act", "")
    if action == "pend":
        __minions_pending[minion_id] = datetime.datetime.now()
        log.debug(f"Added {minion_id} as pending")
    elif action == "accept" and minion_id in __minions_pending:
        del __minions_pending[minion_id]
        log.debug(f"Removed {minion_id} from pending")
    salt_master_minions_count.labels("pending").set(len(__minions_pending))


def job_succeeded(data: dict):
    retcode = data.get("retcode", 0)
    return retcode == 0


def register_event(event):
    log.debug(f"Got event: {event}")
    tag = event.get("tag", "__notag__")
    data = event.get("data", {})
    if type(event) is not dict:
        log.debug("Event is not a dict, skipping")
        return
    if tag == "__notag__":
        log.debug("Event has no tag, skipping")
        return
    if "data" == {}:
        log.debug("Event has no data, skipping")
        return
    if tag == "salt/presence/present":
        register_presence(data)
    elif tag == "minion_ping":
        register_ping(data)
    elif tag == "salt/auth":
        register_authorization(data)
    elif tag.startswith("salt/job") and "/ret/" in tag:
        register_function_call(data)
        if not job_succeeded(data):
            register_failed_job(data)
