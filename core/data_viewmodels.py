from datetime import datetime


class NodeTimeseriesListViewModel:
    def __init__(
        self,
        pk,
        node_alias: str,
        sample_count: int,
        query_timestamp_s: int = round(datetime.now().timestamp()),
        from_timestamp_s: int = 0,
        to_timestamp_s: int = round(datetime.now().timestamp()),
    ):
        self.pk = pk
        self.node_alias = node_alias
        self.sample_count = sample_count
        self.query_timestamp_s = query_timestamp_s
        self.from_timestamp_s = from_timestamp_s
        self.to_timestamp_s = to_timestamp_s

    class JSONAPIMeta:
        resource_name = "node-timeseries"


class NodeTimeseriesViewModel(NodeTimeseriesListViewModel):
    def __init__(
        self,
        pk,
        node_alias: str,
        samples,
        query_timestamp_s: int = round(datetime.now().timestamp()),
        from_timestamp_s: int = 0,
        to_timestamp_s: int = round(datetime.now().timestamp()),
    ):
        super().__init__(
            pk=pk,
            node_alias=node_alias,
            sample_count=len(samples),
            query_timestamp_s=query_timestamp_s,
            from_timestamp_s=from_timestamp_s,
            to_timestamp_s=to_timestamp_s,
        )
        self.samples = samples


class InstallationTimeseriesListViewModel:
    def __init__(
        self,
        pk,
        node_id,
        node_alias: str,
        sample_count: int,
        query_timestamp_s: int = round(datetime.now().timestamp()),
        from_timestamp_s: int = 0,
        to_timestamp_s: int = round(datetime.now().timestamp()),
    ):
        self.pk = pk
        self.node_id = node_id
        self.node_alias = node_alias
        self.sample_count = sample_count
        self.query_timestamp_s = query_timestamp_s
        self.from_timestamp_s = from_timestamp_s
        self.to_timestamp_s = to_timestamp_s

    class JSONAPIMeta:
        resource_name = "installation-timeseries"


class InstallationTimeseriesViewModel(InstallationTimeseriesListViewModel):
    def __init__(
        self,
        pk,
        node_id,
        node_alias: str,
        samples,
        query_timestamp_s: int = round(datetime.now().timestamp()),
        from_timestamp_s: int = 0,
        to_timestamp_s: int = round(datetime.now().timestamp()),
    ):
        super().__init__(
            pk=pk,
            node_id=node_id,
            node_alias=node_alias,
            sample_count=len(samples),
            query_timestamp_s=query_timestamp_s,
            from_timestamp_s=from_timestamp_s,
            to_timestamp_s=to_timestamp_s,
        )
        self.samples = samples

class RoomAirQualityViewModel:
    def __init__(
        self,
        pk,
        analysis_month: str,
        clean_air_medal,
        airq_hist,
        query_timestamp_s: int = round(datetime.now().timestamp()),
        from_timestamp_s: int = 0,
        to_timestamp_s: int = round(datetime.now().timestamp()),
    ):
        self.pk = pk
        self.analysis_month = analysis_month
        self.query_timestamp_s = query_timestamp_s
        self.from_timestamp_s = from_timestamp_s
        self.to_timestamp_s = to_timestamp_s
        self.clean_air_medal = clean_air_medal
        self.airq_hist=airq_hist

    class JSONAPIMeta:
        resource_name = "room-airquality"