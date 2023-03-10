# salt-master-metrics
A daemon that listens for salt-server events and exposes metrics based on them.

## Build

* `pip install build`
* `python3.9 -m build`

## Install

Install on the same machine (container) where salt-master runs.

`salt-pip -m pip install ./salt_master_metrics-*.whl`

## Run

`/opt/saltstack/salt/pypath/bin/salt-master-metrics`

Configuration parameters (environment variables, all with prefix `SALT_MASTER_METRICS_`):

* `LISTEN_PORT` (default `2112`)
* `MASTER_CONFIG_FILE` (default `/etc/salt/master`)
* `LOG_LEVEL` (default `INFO`, see [levels](https://docs.python.org/3/library/logging.html#levels))

## Metrics exposed

* `salt_master_connected_minions_count` - Quantity of currently connected minions.
* `salt_master_pending_minions_count` - Quantity of minions currently pending authorization.
* `salt_master_function_call_count_total{fun="..."}` - How many times the function was called.
* `salt_master_job_failed_total{fun="...",minion="...",jid="...",name="...",comment="...",sls="..."}` - Registered job failure. `name` label stands for name of the state, `sls` label shows which state file the state was called from.
