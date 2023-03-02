# salt-master-metrics
A daemon that listens for salt-server events and exposes metrics based on them.

## Usage

* Copy files to the container where salt-master is running
* Run `/opt/saltstack/salt/run/run python ./main.py`

Configuration parameters (environment variables):

* `SALT_MASTER_METRICS_LISTEN_PORT` (default 2112)
* `SALT_MASTER_METRICS_MASTER_CONFIG_FILE` (default /etc/salt/master)

## Metrics exposed

* `salt_events_total{success}` - count of return events with success result
* `salt_events_total{success, fun}` - count of return events with function label
* `failure_event_created{minion, jid, fun, fun_args}` - timestamp when a failure return event was caught
