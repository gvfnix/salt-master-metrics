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

* `LISTEN_PORT` (default `2112`).
* `MASTER_CONFIG_FILE` (default `/etc/salt/master`).
* `LOG_LEVEL` (default `INFO`, see [levels](https://docs.python.org/3/library/logging.html#levels)).
* `MINION_PING_TIMEOUT` (default `90s`) - interval to wait a ping from a minion until it is considered disconnected.
* `FAILURE_EVENT_RETENTION_INTERVAL` (default `1d`) - interval to store a failure event.

Intervals should be defined as number of seconds, minutes, hours or days, e.g. `90s`, `3m`, `1h`, `2d`.

## Metrics exposed

* `salt_master_minions_count{state}` - `connected` or `pending` minions count.
* `salt_master_function_call_count_total{fun="..."}` - How many times the function was called.
* `salt_master_job_failed_total{comment="...",fun="...",jid="...",minion="...",name="...",sls="..."}` - Registered job failure.

### salt_master_minions_count

This gauge shows how many minions are currently in `pending` or `connected` state.

#### connected

Requires `presence_events` parameter to be enabled on salt master.
Minions are counted by `salt/presece/present` and `minion_ping` events. If there are no pings from a minion for some time(see configuration), then it is considered disconnected.

#### pending

This gauge shows how many minions are currently waiting to be authorized by master. Gauge is increased when `salt/auth` event gets received with `"act": "pend`, and decreased when `salt/auth`event gets received with `"act": "accept"`.

### salt_master_function_call_count_total

This counter shows how many times a function `fun` was called. Counter goes up every time when `salt/job/<JID>/ret/<MINION_ID>` event gets received.

### salt_master_job_failed_total

Samples of this counter always have the value 1.0 and get cleared after 3 minutes (when new failure event arrives). A job is consider failed when `salt/job/<JID>/ret/<MINION_ID>` event gets received with `retcode` != 0.

Labels:

* `comment` - the comment or traceback which was emmitted when the state failed.
* `fun` - function that was called (like `state.apply` or `file.read`).
* `jid` - job id (it can be shown in detail with `salt-run jobs.lookup_jid <JID>`).
* `minion` - minion id which returned the failure event.
* `name` - name of the state.
* `sls` - state file the state was called from.
