# Local Imports
import main
import auxiliary_classes
# External Imports
from paramiko import SSHClient, AutoAddPolicy
import time
import threading


class Session:
    def __init__(self, host, user, password):
        self.user = user
        self.password = password
        self.host = host
        self.is_connected = False
        self.ssh = SSHClient()
        self.flag_stop = False
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        self.ssh.load_system_host_keys()
        self.cpu_usage = []
        self.cpu_number = 0
        self.threads = []
        self.mpid = []

    def connect(self):
        self.ssh.connect(self.host, username=self.user, password=self.password)

    def start_threads(self):
        threading.Thread(target=self.gen_cpu_stats).start()
        auxiliary_classes.global_data.progress.step(10)
        threading.Thread(target=self.gen_ram_stats).start()
        auxiliary_classes.global_data.progress.step(10)
        threading.Thread(target=self.gen_disk_stats).start()
        auxiliary_classes.global_data.progress.step(10)

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

    def start_project(self, file_path, file_name, no_pid = True, fix_permissions = True):
        path = file_path[1:file_path.rfind("/")] + "/"
        real_file_name = file_path[file_path.rfind("/") + 1:]
        stdin, stdout, stderr = self.ssh.exec_command(
            f'cd {path} && ./"{real_file_name}" & echo "pid:"$! && wait && echo "Command was completed"', get_pty=True)
        for response in iter(stdout.readline, ""):
            print(response)
            if no_pid:
                if "pid" in response:
                    auxiliary_classes.global_data.name_pid[file_name] = int(response.split(":")[1])
                    print(auxiliary_classes.global_data.name_pid[file_name])
                    no_pid = False
            if fix_permissions:
                if "Permission denied" in response:
                    self.ssh.exec_command(F"cd {path} && chmod +x '{real_file_name}'")
                    self.start_project(file_path, file_name, False, False)
                    if not auxiliary_classes.global_data.task_done:
                        auxiliary_classes.global_data.task_denied = True
                    return
            if "Command was completed" in response:
                print(f"Task \"{file_name}\" terminada por")
                auxiliary_classes.global_data.task_done = True
                return

    # def pause_process(self, name):
    #     self.ssh.exec_command(f'kill -SIGTSTP {data_class.name_mpid[name]}')

    # def resume_process(self, name):
    #     self.ssh.exec_command(f'kill -SIGCONT {data_class.name_mpid[name]}')

    def stop_process(self, path):
        path = "."+path[:path.rfind('/')+1]
        self.ssh.exec_command(f'cd {path} && touch FDSTOP')
        auxiliary_classes.global_data.task_stopped = True

    def get_mpid_byname(self, name):
        print(f'ps -p {auxiliary_classes.global_data.name_pid[name]} -o ppid')
        stdin, stdout, stderr = self.ssh.exec_command(f'pgrep mpid', get_pty=True)
        for mpid in iter(stdout.readline, ""):
            print("THIS IS MPID:" + str(mpid))
            auxiliary_classes.global_data.name_mpid[name] = int(mpid)
            auxiliary_classes.global_data.has_mpid = True

    def get_cpu_num(self):
        stdin, stdout, stderr = self.ssh.exec_command('grep -c ^processor /proc/cpuinfo', get_pty=True)
        for line in iter(stdout.readline, ""):
            line = int(line)
            self.cpu_number = line
            return line

    def kill_process(self, name):
        self.ssh.exec_command(f'kill -SIGKILL {auxiliary_classes.global_data.name_pid[name]}')
        auxiliary_classes.global_data.task_canceled = True

    def gen_cpu_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('mpstat -P ALL 1', get_pty=True)
        self.is_connected = True
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            if len(line) > 1:
                if line[2].isdigit():
                    self.cpu_usage.append(str(round(float(line[3]))) + "%")
                    if int(line[2]) == self.cpu_number - 1:
                        self.update_gui_values(self.cpu_usage)
                        self.cpu_usage = []
        self.ssh.close()
        self.is_connected = False

    def gen_ram_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('free -t -m -s 5', get_pty=True)
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            if "Mem:" in line:
                line = line.split()
                auxiliary_classes.global_data.ram_stats[0].config(text=line[1] + "MB")
                auxiliary_classes.global_data.ram_stats[1].config(text=line[2] + "MB")
                auxiliary_classes.global_data.ram_stats[2].config(text=line[3] + "MB")
                auxiliary_classes.global_data.ram_stats[3].config(text=str(100 * (int(line[2]) / int(line[1])))[:5] + "%")

    def gen_disk_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('df -h /home && while sleep 5; do df -h /home; done',
                                                      get_pty=True)
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            if len(line) > 1:
                if "G" in line[0]:
                    auxiliary_classes.global_data.disk_storage[0].config(text=line[0] + "B")
                    auxiliary_classes.global_data.disk_storage[1].config(text=line[1] + "B")
                    auxiliary_classes.global_data.disk_storage[2].config(text=line[2] + "B")
                    auxiliary_classes.global_data.disk_storage[3].config(text=line[3])
                elif "G" in line[1]:
                    auxiliary_classes.global_data.disk_storage[0].config(text=line[1] + "B")
                    auxiliary_classes.global_data.disk_storage[1].config(text=line[2] + "B")
                    auxiliary_classes.global_data.disk_storage[2].config(text=line[3] + "B")
                    auxiliary_classes.global_data.disk_storage[3].config(text=line[4])

    def update_gui_values(self, values):
        for x in range(self.cpu_number):
            auxiliary_classes.global_data.cpu_list[x].config(text=values[x])
