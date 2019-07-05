# coding=utf-8
import os
import time

from wetstat.common import config, logger
from wetstat.model import util

MIN_AGE = 24 * 60 * 60  # one day as seconds

plotfolder = os.path.join(config.get_staticfolder(), "plot")
threshold = time.time() - MIN_AGE


def cleanup():
    try:
        removed = 0
        freed_bytes = 0
        for f in os.listdir(plotfolder):
            absfile = os.path.join(plotfolder, f)
            atime = os.path.getatime(absfile)
            if atime < threshold:
                freed_bytes += os.path.getsize(absfile)
                os.remove(absfile)
                removed += 1
        if removed:
            logger.log.info(
                f"{removed} plots ({util.human_readable_size(freed_bytes)}) removed because "
                f"they were older than {MIN_AGE} seconds.")
        else:
            logger.log.info("No plots removed.")
    except Exception as e:
        logger.log.exception(f"Exception in plot_cleanup: {e.args}")
