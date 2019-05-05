# coding=utf-8
import os
import subprocess
import sys
from typing import List


class InfoCommand:
    def get_output_of_command(self, command: List[str], columns=512):
        myenv = os.environ.copy()
        myenv["TERM"] = "linux"
        myenv["COLUMNS"] = str(columns)
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, env=myenv)
        out, err = pipe.communicate()
        out = out.decode()
        if err is not None:
            err = err.decode()
        return out if len(out) > 0 else err

    def get_system(self):
        return sys.platform

    def get_command(self) -> List[str]:
        raise NotImplementedError

    def get_output(self) -> str:
        return self.get_output_of_command(self.get_command())


class ListOfAllProcesses(InfoCommand):

    def get_command(self) -> List[str]:
        if self.get_system() == "win32":
            return ["tasklist"]
        else:
            return ["top", "-n 1", "-b"]


class SystemInfo(InfoCommand):

    def get_command(self) -> List[str]:
        if self.get_system() == "win32":
            return ["systeminfo"]
        else:
            return ["cat", "/etc/os-release"]


class RamInfo(InfoCommand):

    def get_command(self) -> List[str]:
        if self.get_system() == "win32":
            return ["wmic", "get TotalVisibleMemorySize,FreePhysicalMemory"]
        else:
            return ["free", "-h"]


class DiskUsageInfo(InfoCommand):

    def get_command(self) -> List[str]:
        if self.get_system() == "win32":
            return ["wmic", "logicaldisk", "get volumename,name,size,freespace"]
        else:
            return ["df", "-h"]


ALL_INFO_CLASSES = [ListOfAllProcesses(),
                    SystemInfo(),
                    RamInfo(),
                    DiskUsageInfo(),
                    ]
