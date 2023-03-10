from unittest import TestCase, mock
from salt_master_metrics import metrics
from prometheus_client import REGISTRY
from datetime import datetime, timedelta


class TestMetrics(TestCase):


    def setUp(self):
        metrics.clear()

    def test_presence_current(self):
        ping_1 = {
            "tag": "minion_ping",
            "data": {
                "id": "minion_1"
            }
        }
        presence = {
            "tag": "salt/presence/present",
            "data": {
                "present": ["local"]
            }
        }
        metrics.register_event(ping_1)
        metrics.register_event(presence)
        minions_connected = REGISTRY.get_sample_value(
            'salt_master_connected_minions_count'
        )
        self.assertEqual(minions_connected, 2.0)

    @mock.patch("salt_master_metrics.metrics.datetime")
    def test_presence_past(self, mock_datetime):
        mock_datetime.timedelta = timedelta
        now = datetime.now()
        mock_datetime.datetime.now.return_value = now
        ping_1 = {
            "tag": "minion_ping",
            "data": {
                "id": "minion_1"
            }
        }
        presence = {
            "tag": "salt/presence/present",
            "data": {
                "present": ["local"]
            }
        }
        metrics.register_event(ping_1)
        mock_datetime.datetime.now.return_value = now + timedelta(minutes=3)
        metrics.register_event(presence)
        minions_connected = REGISTRY.get_sample_value(
            'salt_master_connected_minions_count'
        )
        self.assertEqual(minions_connected, 1.0)

    def test_pending_minion(self):
        pend = {
            "tag": "salt/auth",
            "data": {
                "act": "pend",
                "id": "minion_1"
            }
        }
        accept = {
            "tag": "salt/auth",
            "data": {
                "act": "accept",
                "id": "minion_1"
            }
        }
        metrics.register_event(pend)
        salt_master_pending_minions_count = REGISTRY.get_sample_value(
            "salt_master_pending_minions_count"
        )
        self.assertEqual(salt_master_pending_minions_count, 1.0)
        metrics.register_event(accept)
        salt_master_pending_minions_count = REGISTRY.get_sample_value(
            "salt_master_pending_minions_count"
        )
        self.assertEqual(salt_master_pending_minions_count, 0.0)

    def test_job_return_success(self):
        event = {
            'data': {
                'cmd': '_return', 
                'id': 'minion_1', 
                'fun': 'state.apply', 
                'fun_args': [], 
                'schedule': 'apply', 
                'jid': '20230310030058447023', 
                'pid': 298843, 
                'return': {}, 
                'retcode': 0, 
                'success': True, 
                '_stamp': '2023-03-10T03:00:58.450041', 
                'out': 'highstate', 
                'arg': [], 
                'tgt_type': 'glob', 
                'tgt': 'minion_1'
            }, 
            'tag': 'salt/job/20230310030058447023/ret/minion_1'
        }
        metrics.register_event(event)
        state_apply_count = REGISTRY.get_sample_value(
            'salt_master_function_call_count_total',
            {"fun": "state.apply"}
        )
        state_apply_failed =  REGISTRY.get_sample_value(
            'salt_master_job_failed_total',
            {
                "fun": "state.apply",
                "jid": "20230310030058447023",
                "minion": "minion_1"
            }
        )
        self.assertEqual(state_apply_count, 1.0)
        self.assertIsNone(state_apply_failed)

    def test_job_return_failure(self):
        event = {
            'data': {
                'cmd': '_return', 
                'id': 'minion_1', 
                'fun': 'state.apply', 
                'fun_args': [], 
                'schedule': 'apply', 
                'jid': '20230310030058447023', 
                'pid': 298843, 
                'return': {}, 
                'retcode': 0, 
                'success': False, 
                '_stamp': '2023-03-10T03:00:58.450041', 
                'out': 'highstate', 
                'arg': [], 
                'tgt_type': 'glob', 
                'tgt': 'minion_1'
            }, 
            'tag': 'salt/job/20230310030058447023/ret/minion_1'
        }
        metrics.register_event(event)
        state_apply_count = REGISTRY.get_sample_value(
            'salt_master_function_call_count_total',
            {"fun": "state.apply"}
        )
        state_apply_failed =  REGISTRY.get_sample_value(
            'salt_master_job_failed_total',
            {
                "fun": "state.apply",
                "jid": "20230310030058447023",
                "minion": "minion_1"
            }
        )
        self.assertEqual(state_apply_count, 1.0)
        self.assertEqual(state_apply_failed, 1.0)

    def test_nonregistered_event(self):
        event = {
            'data': {
                'Minion data cache refresh': 'minion_1', 
                '_stamp': '2023-03-10T03:04:38.684129'
                }, 
            'tag': 'minion/refresh/minion_1'
        }
        metrics.register_event(event)
        minions_connected = REGISTRY.get_sample_value(
            'salt_master_connected_minions_count'
        )
        self.assertEqual(minions_connected, 0.0)
        salt_master_pending_minions_count = REGISTRY.get_sample_value(
            "salt_master_pending_minions_count"
        )
        self.assertEqual(salt_master_pending_minions_count, 0.0)
        state_apply_count = REGISTRY.get_sample_value(
            'salt_master_function_call_count_total',
            {"fun": "state.apply"}
        )
        state_apply_failed =  REGISTRY.get_sample_value(
            'salt_master_job_failed_total',
            {
                "fun": "state.apply",
                "jid": "20230310030058447023",
                "minion": "minion_1"
            }
        )
        self.assertIsNone(state_apply_count)
        self.assertIsNone(state_apply_failed)

