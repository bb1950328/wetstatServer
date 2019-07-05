# coding=utf-8
import os
import subprocess
import sys
from time import strftime, time
from typing import List

from wetstat.common import config


class InfoCommand:
    @staticmethod
    def get_output_of_command(command: List[str], columns=512):
        myenv = os.environ.copy()
        myenv["TERM"] = "linux"
        myenv["COLUMNS"] = str(columns)
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, env=myenv)
        out, err = pipe.communicate()
        out = out.decode(errors="replace")
        out = out.replace("\r\n", "<br>")
        if err is not None:
            err = err.decode()
        return out if len(out) > 0 else err

    @staticmethod
    def get_system() -> str:
        return sys.platform

    def get_command(self) -> List[str]:
        raise NotImplementedError

    def get_output(self) -> str:
        return self.get_output_of_command(self.get_command())


class ListOfAllProcesses(InfoCommand):

    def get_command(self) -> List[str]:
        if not config.on_pi():
            return ["tasklist"]
        else:
            return ["top", "-n 1", "-b"]


class SystemInfo(InfoCommand):

    def get_command(self) -> List[str]:
        if not config.on_pi():
            return ["systeminfo"]
        else:
            return ["cat", "/etc/os-release"]


class RamInfo(InfoCommand):

    def get_command(self) -> List[str]:
        if not config.on_pi():
            return ["wmic", "get TotalVisibleMemorySize,FreePhysicalMemory"]
        else:
            return ["free", "-h"]


class DiskUsageInfo(InfoCommand):

    def get_command(self) -> List[str]:
        if not config.on_pi():
            return ["wmic", "logicaldisk", "get volumename,name,size,freespace"]
        else:
            return ["df", "-h"]


class TimeInfo(InfoCommand):

    def get_command(self) -> List[str]:
        return ["time.strftime()"]

    def get_output(self) -> str:
        return strftime("%A, %d.%m.%Y %H:%M:%S.") + str(time()).split(".")[1]


class NetworkInfo(InfoCommand):
    def get_command(self) -> List[str]:
        return ["ipconfig"] if not config.on_pi() else ["ifconfig"]


ALL_INFO_CLASSES = [ListOfAllProcesses(),
                    SystemInfo(),
                    RamInfo(),
                    NetworkInfo(),
                    DiskUsageInfo(),
                    TimeInfo(),
                    ]
