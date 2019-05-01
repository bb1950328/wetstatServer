# coding=utf-8
from wetstat import system_info

for cls in system_info.ALL_INFO_CLASSES:
    print(cls.get_output())
    print("-" * 80)
