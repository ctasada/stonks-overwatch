import logging


class StonksLogger:
    _instances = {}

    def __new__(cls, name: str, prefix: str):
        if name not in cls._instances:
            instance = super(StonksLogger, cls).__new__(cls)
            instance.logger = logging.getLogger(name)
            instance.prefix = prefix
            cls._instances[name] = instance
        return cls._instances[name]

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(f"{self.prefix} {msg}", *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(f"{self.prefix} {msg}", *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(f"{self.prefix} {msg}", *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(f"{self.prefix} {msg}", *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(f"{self.prefix} {msg}", *args, **kwargs)

    @classmethod
    def get_logger(cls, name: str, prefix: str):
        return cls(name, prefix)
