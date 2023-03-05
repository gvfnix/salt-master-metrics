# salt-master-metrics
A daemon that listens for salt-server events and exposes metrics based on them.

## Build

* `pip install build`
* `python3.9 -m build`

## Install

Install on the same machine (container) where salt-master runs.

`python -m pip install ./salt_master_metrics-*.whl`

## Run

`/opt/saltstack/salt/pypath/bin/salt-master-metrics`

Configuration parameters (environment variables, all with prefix `SALT_MASTER_METRICS_`):

* `LISTEN_PORT` (default `2112`)
* `MASTER_CONFIG_FILE` (default `/etc/salt/master`)
* `LOG_LEVEL` (default `INFO`, see [levels](https://docs.python.org/3/library/logging.html#levels))

## Metrics exposed

* `salt_new_jobs_total{fun}` - counter of new jobs.
* `salt_minion_failed_job_created{jid, minion, fun}` - event of minion failed job.
* `salt_minions_connected` - current quantity of minions connected. Requires [presence_events](https://docs.saltproject.io/en/latest/ref/configuration/master.html#presence-events) enabled in Salt master configuration, otherwise will be always 0.
* `salt_minions_pending_auth` - current quanity of minions not accepted by master.
