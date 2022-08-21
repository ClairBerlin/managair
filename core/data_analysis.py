import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def resample_node_samples(timeseries):
    data = [
        {"timestamp_s": sample.timestamp_s, "co2_ppm": sample.co2_ppm}
        for sample in timeseries
    ]
    samples = pd.DataFrame(data)
    samples["timestamp_s"] = pd.to_datetime(samples["timestamp_s"], unit="s")
    logger.debug(samples.info())
    return samples
