import re
from rest_framework_json_api.filters import QueryParameterValidationFilter


class IncludeTimeseriesQPValidator(QueryParameterValidationFilter):
    """Query parameter validator that admits an extra `include_timeseries` parameter."""

    query_regex = re.compile(
        r"^(sort|include|include_timeseries)$|^(?P<type>filter|fields|page)(\[[\w\.\-]+\])?$"
    )