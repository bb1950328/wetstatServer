# coding=utf-8
import os
import time

import gc
import psutil

from wetstat.model import log_parser

gc.disable()

NUM = 100

start = time.perf_counter()
for i in range(NUM):
    log_parser.parse()
end = time.perf_counter()
print((end - start) / NUM)

process = psutil.Process(os.getpid())
print(process.memory_info())  # in bytes
