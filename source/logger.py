import logging
import os
import sys

from dotenv import load_dotenv


class LoggerMixin:
    """
    The `LoggerMixin` class is a mixin that can be used to add logging capabilities to other classes.

    Usage:
        To use the `LoggerMixin`, simply inherit from it and call the `__init__` method.

    Example:
        ```
        class MyClass(LoggerMixin):
            def __init__(self):
                super().__init__()

            def my_method(self):
                self.log.debug("Debug message")
                self.log.info("Information message")
                self.log.warning("Warning message")
                self.log.error("Error message")
        ```

        In the above example, `MyClass` inherits from `LoggerMixin` and has access to a logger instance via the `self.log` attribute. The logger is configured with a specified log level, format, encoding, and output stream.

    Attributes:
        log (logging.Logger): The logger instance.

    Methods:
        __init__(): Initializes the logger mixin by setting up the log level, format, encoding, and output stream.

    Logging Configuration:
        The log level is determined by the value of the `LOGLEVEL` environment variable. If the environment variable is not set, the default log level is "INFO".
        The log format is set to "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s".
        The log encoding is set to "utf-8".
        The log output stream is set to `sys.stdout`.
    """

    def __init__(self):
        load_dotenv()
        loglevel = os.environ.get("LOGLEVEL", "INFO").upper()
        logging.basicConfig(
            format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            encoding="utf-8",
            level=loglevel,
            stream=sys.stdout,
        )
        self.log = logging.getLogger(self.__class__.__name__)
