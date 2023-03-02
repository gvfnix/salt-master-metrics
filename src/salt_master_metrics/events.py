def register_event(event: dict) -> [dict]:
    if type(event) is not dict:
        return []
    if event.get("cmd") != "_return":
        return []
    else:
        return [
            *register_success_event(event),
            *register_failure_event_counter(event),
            *register_failure_event_detailed(event)
        ]


def register_success_event(event: dict) -> [dict]:
    success = event.get("success")
    if success:
        return [{
            "_type": "total",
            "labels": {
                "success": str(success).lower(),
                "fun": "",
            }
        }]
    else:
        return []


def register_failure_event_counter(event: dict) -> [dict]:
    success = event.get("success")
    if not success:
        return [{
            "_type": "total",
            "labels": {
                "success": str(success).lower(),
                "fun": event.get("fun", "")
            }
        }]
    else:
        return []


def register_failure_event_detailed(event: dict) -> [dict]:
    success = event.get("success")
    if not success:
        return [{
            "_type": "failure",
            "labels": {
                "fun": event.get("fun", ""),
                "minion": event.get("id", ""),
                "jid": event.get("jid", ""),
                "fun_args": " -> ".join(event.get("fun_args", []))
            }
        }]
    else:
        return []
