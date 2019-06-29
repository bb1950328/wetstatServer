# coding=utf-8
import time

from wetstat.model import log_parser

NUM = 100

start = time.perf_counter()
for i in range(NUM):
    log_parser.parse()
end = time.perf_counter()
print((end - start) / NUM)
