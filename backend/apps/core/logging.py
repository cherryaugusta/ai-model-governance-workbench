from logging import Filter


class CorrelationIdLogFilter(Filter):
    def filter(self, record):
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "n/a"
        return True