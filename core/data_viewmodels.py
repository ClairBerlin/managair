from datetime import datetime


class TimeseriesViewModel:
    def __init__(
        self,
        pk,
        alias: str,
        sample_count: int,
        query_timestamp: int = round(datetime.now().timestamp()),
        from_timestamp: int = 0,
        to_timestamp: int = round(datetime.now().timestamp()),
    ):
        self.pk = pk
        self.alias = alias
        self.sample_count = sample_count
        self.query_timestamp = query_timestamp
        self.from_timestamp = from_timestamp
        self.to_timestamp = to_timestamp

    class JSONAPIMeta:
        resource_name = "node-timeseries"


class SamplePageViewModel:
    def __init__(
        self,
        pk,
        alias: str,
        samples,
        query_timestamp: int = round(datetime.now().timestamp()),
        from_timestamp: int = 0,
        to_timestamp: int = round(datetime.now().timestamp()),
    ):
        self.pk = pk
        self.alias = alias
        self.samples = samples
        self.sample_count = len(samples)
        self.query_timestamp = query_timestamp
        self.from_timestamp = from_timestamp
        self.to_timestamp = to_timestamp
