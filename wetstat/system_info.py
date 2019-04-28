# coding=utf-8
import subprocess
import sys


class InfoCommand:
    def get_output_of_command(self, command: str):
        return subprocess.getoutput(command)

    def get_system(self):
        return sys.platform

    def get_command(self) -> str:
        raise NotImplementedError

    def get_output(self) -> str:
        return self.get_output_of_command(self.get_command())


class ListOfAllProcesses(InfoCommand):

    def get_command(self) -> str:
        if self.get_system() == "win32":
            return "tasklist"
        else:
            return "top -n 1"


class SystemInfo(InfoCommand):

    def get_command(self):
        if self.get_system() == "win32":
            return "systeminfo"
        else:
            # TODO find out command
            return ""
