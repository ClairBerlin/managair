from datetime import datetime, timedelta

from core.models import Node


def check_node_fidelity(lookback_interval: timedelta = timedelta(hours=2)):
    lookback_s = lookback_interval.total_seconds()
    check_time_s = round(datetime.now().timestamp())
    nodes = Node.objects.all()
    for node in nodes:
        node.check_fidelity(lookback_interval_s)
