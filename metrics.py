import prometheus_client
total = prometheus_client.Counter(
    "salt_events",
    "Total number of events",
    ["success"]
)
failure = prometheus_client.Counter(
    "salt_failure_event",
    "Detailed failure events",
    ["minion", "jid", "fun", "fun_args"]
)


def register_event(event: dict) -> dict:
    ret = {"count": 0}
    while True:
        if type(event) is not dict:
            break
        cmd = event.get("cmd")
        success = str(event.get("success")).lower()
        if cmd != "_return":
            break
        total_labels = {"success": success}
        total.labels(**total_labels).inc()
        if success == "false":
            failure_labels = {
                "jid": event.get("jid", ""),
                "minion": event.get("id", ""),
                "fun": event.get("fun", ""),
                "fun_args": ",".join(event.get("fun_args", []))
            }
            failure.labels(**failure_labels).inc()
        break
    return ret
