import events
def test_register_success_event_match():
    assert events.register_success_event(
        {"success": True}
    ) == [{
        "_type": "total",
        "labels": {
            "success": "true",
            "fun": ""
        }
    }]

def test_register_success_event_nomatch():
    assert events.register_success_event(
        {"success": False}
    ) == []


def test_register_failure_event_counter_match():
    assert events.register_failure_event_counter(
        {"success": False, "fun": "state.apply"}
    ) == [{
        "_type": "total",
        "labels": {
            "success": "false",
            "fun": "state.apply"
        }
    }]


def test_register_failure_event_counter_nomatch():
    assert events.register_failure_event_counter(
        {"success": True}
    ) == []


def test_register_failure_event_detailed_match():
    assert events.register_failure_event_detailed(
        {
            "success": False,
            "fun": "file.replace",
            "fun_args": ["non-present", "base", "override"],
            "id": "minion1",
            "jid": "101"
        }
    ) == [{
        "_type": "failure",
        "labels": {
            "fun": "file.replace",
            "fun_args": "non-present -> base -> override",
            "minion": "minion1",
            "jid": "101"
        }
    }]


def test_register_event_success():
    assert events.register_event({
        "cmd": "_return",
        "success": True
        }
    ) == [{
        "_type": "total",
        "labels": {
            "success": "true",
            "fun": ""
        }
    }]


def test_register_event_failure():
    registered_events = events.register_event(
        {
            "cmd": "_return",
            "success": False,
            "fun": "file.replace",
            "fun_args": ["non-present", "base", "override"],
            "jid": "101",
            "id": "minion1"
        }
    )
    failure_counter = {
        "_type": "total",
        "labels": {
            "success": "false",
            "fun": "file.replace"
        }
    }
    failure_detailed = {
        "_type": "failure",
        "labels": {
            "fun": "file.replace",
            "fun_args": "non-present -> base -> override",
            "minion": "minion1",
            "jid": "101"
        }
    }
    success_counter = {
        "_type": "total",
        "labels": {
            "success": "true",
            "fun": ""
        }
    }
    assert len(registered_events) == 2
    assert failure_counter in registered_events
    assert failure_detailed in registered_events
    assert success_counter not in registered_events


def test_register_event_none():
    assert events.register_event(None) == []


def test_event_non_return():
    assert events.register_event({"cmd": "_minion_event"}) == []
