# coding=utf-8
import os

from wetstat.common import config, logger
from datetime import datetime, timedelta

plotfolder = os.path.join(config.get_staticfolder(), "plot")
files = list(filter(os.path.isfile,
                    os.listdir(plotfolder)))
split_dt = datetime.now() - timedelta(days=1)
to_delete = []
for f in files:
    fullpath = os.path.join(plotfolder, f)
    lastaccess = datetime.fromtimestamp(os.path.getatime(fullpath))
    if lastaccess < split_dt:
        to_delete.append(fullpath)
if len(to_delete) > 0:
    logger.log.info(f"Deleting {len(to_delete)} plots because they are older than one day")
    for f in to_delete:
        os.remove(f)
