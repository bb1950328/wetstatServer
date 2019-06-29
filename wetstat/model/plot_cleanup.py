# coding=utf-8
import os
import time

from wetstat.common import config, logger

MIN_AGE = 24 * 60 * 60  # one day as seconds

plotfolder = os.path.join(config.get_staticfolder(), "plot")
threshold = time.time() - MIN_AGE


def cleanup():
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
        prefix = ""

        if freed_bytes > 1_000_000_000:  # > 1GB
            freed_bytes = round(freed_bytes / 1_000_000_000, 3)
            prefix = "G"
        elif freed_bytes > 1_000_000:  # > 1MB
            freed_bytes = round(freed_bytes / 1_000_000, 3)
            prefix = "M"
        elif freed_bytes > 1_000:  # > 1KB
            freed_bytes = round(freed_bytes / 1_000, 3)
            prefix = "K"

        logger.log.info(
            f"{removed} plots ({freed_bytes}{prefix}B) removed because they were older than {MIN_AGE} seconds.")
    else:
        logger.log.info("No plots removed.")
