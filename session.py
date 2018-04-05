# External Imports
from tkinter import *
from paramiko import SSHClient, AutoAddPolicy
import time
import threading

class Session:
    def __init__(self, widgets, host, user, password):
        self.user = user
        self.password = password
        self.widgets = widgets
        self.host = host
        self.is_connected = False
        self.ssh = SSHClient()
        self.flag_stop = False
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh.load_system_host_keys()
        self.cpu_number = 0
        self.threads = []
        self.mpid = []

    def connect(self):
        self.ssh.connect(self.host, username=self.user, password=self.password)

    def start_threads(self):
        threading.Thread(target=self.gen_cpu_stats).start()
        self.widgets.progress.step(10)
        threading.Thread(target=self.gen_ram_stats).start()
        self.widgets.progress.step(10)
        threading.Thread(target=self.gen_disk_stats).start()
        self.widgets.progress.step(10)

    def assert_connection(self):
        # force connection
        time_start = time.time()
        while True:
            try:
                self.connect()
                self.is_connected = True
                return True
            except:
                print(time.time() - time_start)
                if (time.time() - time_start) > 3:
                    self.ssh.close()
                    return False

    def start_project(self, file_path, file_name, no_pid=True, fix_permissions=True, bar_set=False):
        last_val = 0
        path = file_path[1:file_path.rfind("/")] + "/"
        real_file_name = file_path[file_path.rfind("/") + 1:]
        stdin, stdout, stderr = self.ssh.exec_command(
            f'cd {path} && ./"{real_file_name}" & echo "pid:"$! && wait && echo "Command was completed"', get_pty=True)
        self.widgets.cute_tag.config(text="Processing   ")
        self.widgets.progress_project.pack(expand=True, fill=X, side=RIGHT)
        self.widgets.project_name.config(text=file_name)
        for response in iter(stdout.readline, ""):
            print(response)
            response_split = response.split()
            if len(response_split) > 3:
                if response_split[0].isdigit():
                    if not bar_set:
                        try:
                            self.widgets.progress_project.configure(maximum=int(response_split[len(response.split())-1]),
                                                                    value=0)
                            bar_set = True
                        except:
                            print("Error on setting bar")
                            bar_set = False
                try:
                    self.widgets.progress_project.step(int(response_split[0])- last_val)
                    self.widgets.project_iteration.config(text=f"{response_split[0]} of {int(response_split[0]) + int(response_split[len(response.split())-1])}")
                    per_calc = str((int(response_split[0])/(int(response_split[0]) + int(response_split[len(response.split())-1])))*100)
                    self.widgets.project_percentage.config(text=per_calc[:per_calc.find('.')+3])
                    self.widgets.project_etc.config(text=response.split()[len(response_split)-2])
                    last_val = int(response_split[0])
                except:
                    print("Error on bar")
                    pass
            if no_pid:
                if "pid" in response:
                    self.widgets.name_pid[file_name] = int(response.split(":")[1])
                    print(self.widgets.name_pid[file_name])
                    no_pid = False
            if fix_permissions:
                if "Permission denied" in response:
                    self.ssh.exec_command(F"cd {path} && chmod +x '{real_file_name}'")
                    self.start_project(file_path, file_name, False, False)
                    if not self.widgets.task_done:
                        self.widgets.task_denied = True
                    return
            if "Command was completed" in response:
                print(f"Task \"{file_name}\" terminada por")
                self.widgets.task_done = True
                return

    # def pause_process(self, name):
    #     self.ssh.exec_command(f'kill -SIGTSTP {data_class.name_mpid[name]}')

    # def resume_process(self, name):
    #     self.ssh.exec_command(f'kill -SIGCONT {data_class.name_mpid[name]}')

    def stop_process(self, path):
        path = "." + path[:path.rfind('/')+1]
        self.ssh.exec_command(f'cd {path} && touch FDSTOP')
        self.widgets.task_stopped = True

    def remove_fdstop(self, path):
        path = "." + path[:path.rfind('/')+1]
        self.ssh.exec_command(f'cd {path} && rm FDSTOP')

    def get_mpid_byname(self, name):
        print(f'ps -p {self.widgets.name_pid[name]} -o ppid')
        stdin, stdout, stderr = self.ssh.exec_command(f'pgrep mpid', get_pty=True)
        for mpid in iter(stdout.readline, ""):
            print("THIS IS MPID:" + str(mpid))
            self.widgets.name_mpid[name] = int(mpid)

    def get_cpu_num(self):
        stdin, stdout, stderr = self.ssh.exec_command('grep -c ^processor /proc/cpuinfo', get_pty=True)
        for line in iter(stdout.readline, ""):
            line = int(line)
            self.cpu_number = line
            return line

    def kill_process(self, name):
        self.ssh.exec_command(f'kill -SIGKILL {self.widgets.name_pid[name]}')
        self.widgets.task_canceled = True

    def gen_cpu_stats(self):
        cpu_usage = []
        stdin, stdout, stderr = self.ssh.exec_command('mpstat -P ALL 1', get_pty=True)
        self.is_connected = True
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            try:
                if len(line) > 1:
                    if float(line[2]) != "nan":
                        cpu_usage.append(str(round(float(line[3]))))
                        if int(line[2]) == self.cpu_number - 1:
                            self.update_gui_values(cpu_usage)
                            del cpu_usage[:]
            except ValueError:
                pass
        self.ssh.close()
        self.is_connected = False

    def gen_ram_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('free -t -m -s 5', get_pty=True)
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            if "Mem:" in line:
                line = line.split()
                usage = (100 * (int(line[2]) / int(line[1])))
                if "G" in line[0]:
                    i = 0
                elif "G" in line[1]:
                    i = 1
                if usage < 60:
                    color = "green"
                elif 60 <= usage < 90:
                    color = "orange"
                else:
                    color = "red"
                self.widgets.ram_stats_0.config(text=line[1] + "MB")
                self.widgets.ram_stats_1.config(text=line[2] + "MB")
                self.widgets.ram_stats_2.config(text=line[3] + "MB")
                self.widgets.ram_stats_3.config(text=str(usage)[:5] + "%", foreground=color)

    def gen_disk_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('df -h /home && while sleep 5; do df -h /home; done',
                                                      get_pty=True)
        i = 0
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            if len(line) > 1:
                if "G" in line[0]:
                    i = 0
                elif "G" in line[1]:
                    i = 1
                try:
                    usage = int(line[3+i][:line[3+i].find("%")])
                    if usage < 60:
                        color = "green"
                    elif 60 <= usage < 90:
                        color = "orange"
                    else:
                        color = "red"
                    self.widgets.disk_storage_0.config(text=line[0+i] + "B")
                    self.widgets.disk_storage_1.config(text=line[1+i] + "B")
                    self.widgets.disk_storage_2.config(text=line[2+i] + "B")
                    self.widgets.disk_storage_3.config(text=line[3+i], foreground=color)
                except:
                    pass

    def update_gui_values(self, values):
        self.widgets.cpu_stats_0.config(text=values[0] + "%")
        self.widgets.cpu_stats_1.config(text=values[1] + "%")
        self.widgets.cpu_stats_2.config(text=values[2] + "%")
        self.widgets.cpu_stats_3.config(text=values[3] + "%")
        avg = round((int(values[0])+int(values[1])+int(values[2])+int(values[3]))/4)
        if avg < 60:
            color = "green"
        elif 60 <= avg < 90:
            color = "orange"
        else:
            color = "red"
        self.widgets.cpu_avg.config(text=str(avg)+"%", foreground = color)

