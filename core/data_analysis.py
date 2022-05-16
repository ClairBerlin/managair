import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def resample_node_samples(time_series):
    data = [ {"timestamp_s": sample.timestamp_s, "co2_ppm": sample.co2_ppm} for sample in time_series]
    samples = pd.DataFrame(data)
    logger.debug(samples.info())
