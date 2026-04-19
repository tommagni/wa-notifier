import logging
import time

LOG_FORMAT = 'time="%(asctime)s" level=%(levelname_lc)s msg="%(message)s"'
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class UTCKeyValueFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        record.levelname_lc = record.levelname.lower()
        return super().format(record)
