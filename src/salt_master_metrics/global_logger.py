import logging
import salt_master_metrics.config
import sys
import json


class GlobalLogger(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    
    def __init__(self):
        _config = salt_master_metrics.config.get_config()
        self._log_level = logging.getLevelName(_config.log_level.upper())
        self._handler = logging.StreamHandler(stream=sys.stdout)
        log_format = json.dumps(
            {
                "_timestamp": "%(asctime)s",
                "name": "%(name)s",
                "level": "%(levelname)s",
                "message": "%(message)s",
            }
        )
        formatter = logging.Formatter(log_format)
        self._handler.setFormatter(formatter)

    def getLogger(self, name):
        logger = logging.getLogger(name)
        logger.setLevel(self._log_level)
        logger.addHandler(self._handler)
        return logger


def getLogger(name):
    return GlobalLogger().getLogger(name)

