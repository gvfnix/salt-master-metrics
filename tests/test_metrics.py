import unittest.mock
import datetime
import salt_master_metrics.metrics

class MetricMock(object):

    def __init__(self, name, description="", labels=[]):
        self._name = name
        self._value = 0
        self._labels = {}
    
    def labels(self, **kwargs):
        self._labels = kwargs
        return self

    def inc(self):
        self._value += 1

    def set(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def get_labels(self):
        return self._labels


mocked_metrics = {
    "new_jobs": MetricMock(
        "new_jobs",
        "Total quantity of new jobs",
        ["fun"]
    ),
    "minion_failed_job": MetricMock(
        "minion_failed_job",
        "Failed job events",
        ["minion", "fun", "jid"]
    ),
    "minions_connected": MetricMock(
        "minions_connected",
        "Quantity of currently connected minions"
    ),
    "minions_pending": MetricMock(
        "minions_pending",
        "Quantity of minions pending auth"
    )
}




class TestMetrics(unittest.TestCase):

    def test_register_event(self):
        events = {
            "new_job_1": {
                "tag": "salt/job/1/new",
                "data": {
                    "jid": "1",
                    "fun": "test.ping",
                }
            },
            "failed_job": {
                'tag': 'salt/job/1/ret/local',
                'data': {
                    'success': False,
                    'jid': '1',
                    'id': 'local',
                    'fun': 'state.apply'
                }
            },
            'success_job': {
                'tag': 'salt/job/2/ret/local',
                'data': {
                    'success': True,
                    'jid': '2',
                    'id': 'one',
                    'fun': 'state.apply'
                }
            },
            'presence': {
                'data': {
                    'present': ['local', 'one', 'two'],
                },
                'tag': 'salt/presence/present'
            },
            'pending': {
                'tag': 'salt/auth',
                'data': {
                    'id': 'one',
                    'act': 'pend',
                    'result': True,
                    'pub_key': '...'
                }
            },
            'accepted': {
                'tag': 'salt/auth',
                'data': {
                    'id': 'one',
                    'act': 'accept',
                    'result': True,
                    'pub_key': '...'
                }
            }
        }
        for event in events.values():
            salt_master_metrics.metrics.register_event(event, mocked_metrics)
        assert mocked_metrics["new_jobs"].get_labels() == {"fun": "test.ping"}
        assert mocked_metrics["new_jobs"].get_value() == 1
        assert mocked_metrics["minion_failed_job"].get_labels() == {
            "fun": "state.apply",
            "minion": "local",
            "jid": "1"
        }
        assert mocked_metrics["minion_failed_job"].get_value() == 1
        assert mocked_metrics["minions_connected"].get_value() == 3
        assert mocked_metrics["minions_pending"].get_value() == 0
        
    def test_register_new_job_match(self):
        event = {
            "tag": "salt/job/1/new",
            "data": {
                "jid": "1",
                "fun": "test.ping",
            }
        }
        counter = MetricMock("new_jobs")
        salt_master_metrics.metrics.register_new_job(event, counter)
        assert counter.get_labels() == {"fun": "test.ping"}
        assert counter.get_value() == 1

    def test_register_new_job_notmatch(self):
        event = {
            "tag": "salt/job/1/ret",
            "data": {
                "jid": "1",
                "fun": "test.ping",
            }
        }
        counter = MetricMock("new_jobs")
        salt_master_metrics.metrics.register_new_job(event, counter)
        assert counter.get_labels() == {}
        assert counter.get_value() == 0

    def test_register_failed_job_match(self):
        event = {
            "tag": "salt/job/1/ret/local",
            "data": {
                "success": False,
                "jid": "1",
                "fun": "test.ping",
                "id": "local"
            }
        }
        counter = MetricMock("minion_failed_job")
        salt_master_metrics.metrics.register_failed_job(event, counter)
        assert counter.get_labels() == {
            "minion": "local",
            "jid": "1",
            "fun": "test.ping"
        }
        assert counter.get_value() == 1

    def test_register_failed_job_notmatch(self):
        event = {
            "tag": "salt/job/1/ret/local",
            "data": {
                "success": True,
                "jid": "1",
                "fun": "test.ping",
                "id": "local"
            }
        }
        counter = MetricMock("minion_failed_job")
        salt_master_metrics.metrics.register_failed_job(event, counter)
        assert counter.get_labels() == {}
        assert counter.get_value() == 0

    def test_register_connected_minions(self):
        event = {
            'data': {
                'present': ['local', 'one', 'two'],
            },
            'tag': 'salt/presence/present'
        }
        gauge = MetricMock("minions_connected")
        salt_master_metrics.metrics.register_connected_minions(event, gauge)
        assert gauge.get_value() == 3
        assert gauge.get_labels() == {}

    def test_register_connected_minions_notmatch(self):
        event = {
            'tag': 'salt/some_event'
        }
        gauge = MetricMock("minions_connected")
        salt_master_metrics.metrics.register_connected_minions(event, gauge)
        assert gauge.get_value() == 0
        assert gauge.get_labels() == {}

    def test_register_minion_auth(self):
        auth_pend_event = {
            'tag': 'salt/auth',
            'data': {
                'id': 'local',
                'act': 'pend',
                'result': True,
                'pub_key': '...'
            }
        }
        gauge = MetricMock('minions_pending')
        for _ in range(1,3):
            salt_master_metrics.metrics.register_pending_minions(auth_pend_event, gauge)
        assert gauge.get_value() == 1
        assert gauge.get_labels() == {}
        auth_accept_other_event = {
            'tag': 'salt/auth',
            'data': {
                'id': 'one',
                'act': 'accept',
                'result': True,
                'pub_key': '...'
            }
        }
        salt_master_metrics.metrics.register_pending_minions(auth_accept_other_event, gauge)
        assert gauge.get_value() == 1
        assert gauge.get_labels() == {}
        auth_accept_event = {
            'tag': 'salt/auth',
            'data': {
                'id': 'local',
                'act': 'accept',
                'result': True,
                'pub_key': '...'
            }
        }
        salt_master_metrics.metrics.register_pending_minions(auth_accept_event, gauge)
        assert gauge.get_value() == 0
        assert gauge.get_labels() == {}

    def test_register_minion_auth_notmatch(self):
        event = {'tag': 'some_event'}
        gauge = MetricMock('minions_pending')
        salt_master_metrics.metrics.register_pending_minions(event, gauge)
        assert gauge.get_value() == 0
        assert gauge.get_labels() == {}

    def test_register_minion_ping(self):
        ping1 = {"tag": "minion_ping", "data": {"id": "minion1"}}
        ping2 = {"tag": "minion_ping", "data": {"id": "minion2"}}
        presence = {"tag": "salt/presence/present", "data": {"present": ["salt-master"]}}
        gauge = MetricMock("minions_connected")
        salt_master_metrics.metrics.register_connected_minions(ping1, gauge)
        salt_master_metrics.metrics.register_connected_minions(ping2, gauge)
        salt_master_metrics.metrics.register_connected_minions(presence, gauge)
        assert gauge.get_value() == 3
        threshold = datetime.datetime.now() + datetime.timedelta(minutes=3)
        salt_master_metrics.metrics.register_connected_minions(presence, gauge, threshold)
        assert gauge.get_value() == 1
