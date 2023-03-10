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

    def test_job_return_failure_dict(self):
        event = {
            'data': {
                'cmd': '_return', 
                'id': 'minion_1', 
                'fun': 'state.apply', 
                'fun_args': [], 
                'schedule': 'apply', 
                'jid': '20230310030058447023', 
                'pid': 298843, 
                'return': {
                    "state_1": {
                        "result": True,
                        "__sls__": "main",
                        "__id__": "Working state",
                        "comment": "All good",
                    },
                    "state_2": {
                        "result": False,
                        "__sls__": "main",
                        "__id__": "Failed state",
                        "comment": "Problem detected",
                    },
                }, 
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
        working_state_failure_count =  REGISTRY.get_sample_value(
            'salt_master_job_failed_total',
            {
                "fun": "state.apply",
                "jid": "20230310030058447023",
                "minion": "minion_1",
                "name": "Working state",
                "comment": "All good",
                "sls": "main"
            }
        )
        failed_state_failure_count =  REGISTRY.get_sample_value(
            'salt_master_job_failed_total',
            {
                "fun": "state.apply",
                "jid": "20230310030058447023",
                "minion": "minion_1",
                "name": "Failed state",
                "comment": "Problem detected",
                "sls": "main"
            }
        )
        self.assertEqual(state_apply_count, 1.0)
        self.assertIsNone(working_state_failure_count)
        self.assertEqual(failed_state_failure_count, 1.0)

    def test_failed_job_return_str(self):
        event = {
            'data': 
            {
                'cmd': '_return', 
                'id': 'minion_1', 
                'success': False, 
                'return': "ERROR executing 'file.replace': File not found: /a/b/c/d/e/f", 
                'out': 'nested', 
                'retcode': 1, 
                'jid': '20230310111726726293', 
                'fun': 'file.replace', 
                'fun_args': ['/a/b/c/d/e/f', 'g', 'h'], 
                '_stamp': '2023-03-10T11:17:26.808407'
            }, 
            'tag': 'salt/job/20230310111726726293/ret/minion_1'
        }
        metrics.register_event(event)
        function_call_count = REGISTRY.get_sample_value(
            "salt_master_function_call_count_total",
            {"fun": "file.replace"}
        )
        self.assertEqual(function_call_count, 1.0)
        failed_state_count = REGISTRY.get_sample_value(
            "salt_master_job_failed_total",
            {
                "fun": "file.replace",
                "jid": "20230310111726726293",
                "minion": "minion_1",
                "comment": "ERROR executing 'file.replace': File not found: /a/b/c/d/e/f",
                "name": "",
                "sls": ""
            }
        )
        self.assertEqual(failed_state_count, 1.0)

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

    def test_older_than(self):
        three_mins_ago = datetime.now() - timedelta(minutes=3)
        self.assertTrue(metrics.older_than(three_mins_ago, timedelta(minutes=1)))
        self.assertFalse(metrics.older_than(three_mins_ago, timedelta(minutes=5)))

    @mock.patch("salt_master_metrics.metrics.datetime")
    def test_cleanup_failures(self, mock_datetime):
        now = datetime.now()
        mock_datetime.timedelta = timedelta
        mock_datetime.datetime.now.return_value = now
        failure1 = {
            'data': 
            {
                'cmd': '_return', 
                'id': 'minion_1', 
                'success': False, 
                'return': "ERROR executing 'file.replace': File not found: /mytest", 
                'out': 'nested', 
                'retcode': 1, 
                'jid': '20230310111726726293', 
                'fun': 'file.replace', 
                'fun_args': ['/mytest', 'g', 'h'], 
            }, 
            'tag': 'salt/job/20230310111726726293/ret/minion_1'
        }
        metrics.register_event(failure1)
        failure1_count = REGISTRY.get_sample_value(
            "salt_master_job_failed_total",
            {
                "comment": "ERROR executing 'file.replace': File not found: /mytest",
                "minion": "minion_1",
                "jid": "20230310111726726293",
                "fun": "file.replace",
                "name": "",
                "sls": "",
            }
        )
        self.assertEqual(failure1_count, 1.0)
        failure2 = {
            'data': 
            {
                'cmd': '_return', 
                'id': 'minion_1', 
                'success': False, 
                'return': "ERROR executing 'file.replace': File not found: /mytest", 
                'out': 'nested', 
                'retcode': 1, 
                'jid': '20230310111726726294', 
                'fun': 'file.replace', 
                'fun_args': ['/mytest', 'g', 'h'], 
            }, 
            'tag': 'salt/job/20230310111726726294/ret/minion_1'
        }
        mock_datetime.datetime.now.return_value = now + timedelta(minutes=5)
        metrics.register_event(failure2)
        failure1_count = REGISTRY.get_sample_value(
            "salt_master_job_failed_total",
            {
                "comment": "ERROR executing 'file.replace': File not found: /mytest",
                "minion": "minion_1",
                "jid": "20230310111726726293",
                "fun": "file.replace",
                "name": "",
                "sls": "",
            }
        )
        failure2_count = REGISTRY.get_sample_value(
            "salt_master_job_failed_total",
            {
                "comment": "ERROR executing 'file.replace': File not found: /mytest",
                "minion": "minion_1",
                "jid": "20230310111726726294",
                "fun": "file.replace",
                "name": "",
                "sls": "",
            }
        )
        self.assertIsNone(failure1_count)
        self.assertEqual(failure2_count, 1.0)
