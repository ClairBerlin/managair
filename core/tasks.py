from datetime import datetime, timedelta

from core.models import Node


def check_node_fidelity(lookback_interval: timedelta = timedelta(hours=2)):
    lookback_interval_s = lookback_interval.total_seconds()
    nodes = Node.objects.all()
    for node in nodes:
        node.check_fidelity(lookback_interval_s)
