from datetime import datetime, timedelta

from core.models import Node, Sample, NodeFidelity


def check_node_fidelity(lookback_interval: timedelta = timedelta(hours=2)):
    lookback_s = lookback_interval.total_seconds()
    check_time_s = round(datetime.now().timestamp())
    nodes = Node.objects.all()
    for node in nodes:
        fidelity = {'node' : node,
                    'last_check_s': check_time_s}
        # Retrieve the 2 latest samples.
        latest_sample = Sample.objects.filter(node=node.pk).latest()
        if latest_sample == None:
            fidelity['fidelity'] = NodeFidelity.UNKNOWN
            fidelity['last_contact_s'] = None
        elif (check_time_s - latest_sample.timestamp_s) <= lookback_s:
            fidelity['fidelity'] = NodeFidelity.ALIVE
            fidelity['last_contact_s'] = latest_sample.timestamp_s
        elif ((check_time_s - latest_sample.timestamp_s) <= 2*lookback_s):
            fidelity['fidelity'] = NodeFidelity.MISSING
            fidelity['last_contact_s'] = latest_sample.timestamp_s
        else:
            fidelity['fidelity'] = NodeFidelity.DEAD
            fidelity['last_contact_s'] = latest_sample.timestamp_s
        NodeFidelity.objects.update_or_create(
            node=fidelity['node'], defaults={**fidelity})
    