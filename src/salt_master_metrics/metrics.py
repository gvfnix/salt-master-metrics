import prometheus_client
import datetime
import salt_master_metrics.global_logger


log = salt_master_metrics.global_logger.getLogger(__name__)
salt_master_connected_minions_count = prometheus_client.Gauge(
    "salt_master_connected_minions_count",
    "Quantity of currently connected minions"
)
salt_master_pending_minions_count = prometheus_client.Gauge(
    "salt_master_pending_minions_count",
    "Quantity of minions currently pending authorization"
)
salt_master_function_call_count = prometheus_client.Counter(
    "salt_master_function_call_count",
    "How many times the function was called",
    ["fun"]
)
salt_master_job_failed = prometheus_client.Counter(
    "salt_master_job_failed",
    "Registered job failure",
    ["fun", "minion", "jid", "name", "comment", "sls"]
)
__minions_pending = {}
__minions_ping = {}


def clear():
    __minions_pending = {}
    __minions_ping = {}
    salt_master_connected_minions_count.set(0)
    salt_master_pending_minions_count.set(0)
    salt_master_function_call_count.clear()
    salt_master_job_failed.clear()


def register_function_call(data):
    fun = data.get("fun", "")
    salt_master_function_call_count.labels(fun=fun).inc()


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
                salt_master_job_failed.labels(**labels).inc()
                log.debug(f"Register minion job failure with labels {labels}")
    elif type(_return) is list:
        for comment in _return:
            labels["comment"] = comment
            salt_master_job_failed.labels(**labels).inc()
            log.debug(f"Register minion job failure with labels {labels}")
    elif type(_return) is str:
        labels["comment"] = _return
        salt_master_job_failed.labels(**labels).inc()
        log.debug(f"Register minion job failure with labels {labels}")

def register_presence(data: dict):
    present_minions = data.get("present", [])
    now = datetime.datetime.now()
    recent_pinged_minions = {
        minion_id: ping_time for minion_id, ping_time in __minions_ping.items()
        if (now - ping_time) < datetime.timedelta(seconds=90)
    }
    __minions_ping.clear()
    __minions_ping.update(recent_pinged_minions)
    _value = len(present_minions) + len(__minions_ping)
    salt_master_connected_minions_count.set(_value)


def register_ping(data: dict):
    now = datetime.datetime.now()
    minion_id = data.get("id", "__none__")
    __minions_ping[minion_id] = now


def register_authorization(data):
    minion_id = data.get("id", "")
    action = data.get("act", "")
    if action == "pend":
        __minions_pending[minion_id] = 1
        log.debug(f"Added {minion_id} as pending")
    elif action == "accept"and minion_id in __minions_pending:
        del __minions_pending[minion_id]
        log.debug(f"Removed {minion_id} from pending")
    salt_master_pending_minions_count.set(len(__minions_pending))


def job_succeeded(data:dict):
    success = data.get("success")
    retcode = data.get("retcode")
    log.debug(f"Success: {success}, retcode: {retcode}")
    if success is None:
        return (retcode == 0)
    else:
        return success


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
