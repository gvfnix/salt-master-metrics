import unittest.mock
import events
import counters

class CounterMock(object):
    def __init__(self, name):
        self._name = name
        self._values = {}
        self._labels = ""
    
    def mklabels(self, **kwargs):
        keys=sorted(list(kwargs.keys()))
        _labels = ",".join([f'{k}="{kwargs[k]}"' for k in keys if kwargs[k] != ""])
        return _labels

    def labels(self, **kwargs):
        self._labels = self.mklabels(**kwargs)
        return self

    def inc(self):
        counter_key = f'{self._name}_total{{{self._labels}}}'
        counter_value = self._values.get(counter_key, 0) + 1
        self._values[counter_key] = counter_value

    def stats(self):
        return len(self._values.keys())

    def get(self, **labels):
        counter_key = f'{self._name}_total{{{self.mklabels(**labels)}}}'
        return self._values.get(counter_key, 0)




class TestCounters(unittest.TestCase):
    
    def setUp(self):
        self.counters = {
            "total": CounterMock("salt_return_events"),
            "failure": CounterMock("salt_return_failed")
        }

    def test_update_counters_nonregistered(self):
        registered_events = events.register_event(
            {"cmd": "_minion_event"}
        )
        counters.update_counters(
            self.counters,
            registered_events
        )
        assert self.counters["total"].stats() == 0
        assert self.counters["failure"].stats() == 0

    def test_counters_success(self):
        registered_events = events.register_event(
            {"cmd": "_return", "success": True}
        )
        counters.update_counters(self.counters, registered_events)
        assert self.counters["failure"].stats() == 0
        assert self.counters["total"].stats() == 1
        assert self.counters["total"].get(success="true") == 1

    def test_counters_failure(self):
        event = {
            "cmd": "_return",
            "success": False,
            "fun": "state.apply",
            "fun_args": [],
            "jid": "101",
            "id": "localhost"
        }
        registered_events = events.register_event(event)
        counters.update_counters(self.counters, registered_events)
        total = self.counters["total"]
        failure = self.counters["failure"]
        assert total.stats() == 1
        assert total.get(success="false") == 0
        assert total.get(success="true") == 0
        assert total.get(success="false", fun="state.apply") == 1
        assert failure.stats() == 1
        assert failure.get(fun="state.apply", jid="101", minion="localhost") == 1
