import prometheus_client

prometheus_counters = {
    "total": prometheus_client.Counter(
        "salt_return_events",
        "Return events counter",
        ["success", "fun"]
    ),
    "failure": prometheus_client.Counter(
        "salt_return_failed",
        "Failed return events counter",
        ["minion", "fun", "jid", "fun_args"]
    )
}

def update_counters(counters: [dict] = prometheus_counters, events: [dict] = []):
    for event in events:
        event_type = event["_type"]
        counters[event_type].labels(**event["labels"]).inc()
