from tkinter import *
from tkinter import messagebox, ttk, filedialog
from tkinter.font import Font

import os

import config
from importlib import reload
from ProjectManClass import ProjectSim
import base64
from paramiko import SSHClient, AutoAddPolicy
import threading
from datetime import datetime
import time
import heapq
import pickle

class DDList():
    """ A Tkinter listbox with drag'n'drop reordering of entries. """
    def __init__(self, master, **kw):
        self.SortDir = True
        f = ttk.Frame(master)
        f.pack(fill=BOTH , expand=True)
        self.dataCols = ('Project Name', 'Status', 'Cores', 'Turn', 'Added date/time')
        self.tree = ttk.Treeview(columns=self.dataCols,
                                 show='headings')
        self.mouse_event = None
        self.moved_flag = False
        ysb = ttk.Scrollbar(orient=VERTICAL, command= self.tree.yview)
        self.popup_menu = Menu(master, tearoff=0)
        self.popup_menu.add_command(label="Delete",
                                    command= lambda: self.delete(self.mouse_event))
        self.popup_menu.add_command(label="Stop",
                                    command=lambda: self.do_kill_process(self.mouse_event))
        self.popup_menu.add_command(label="Pause",
                                    command = lambda: self.do_pause_process(self.mouse_event))
        self.popup_menu.add_command(label="Resume",
                                    command=lambda: self.do_resume_process(self.mouse_event))
        self.tree['yscroll'] = ysb.set
        self.tree.grid(in_=f, row=0, column=0, sticky=NSEW)

        ysb.grid(in_=f, row=0, column=1, sticky=NS)

        # set frame resize priorities
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        self._load_data()
        self.tree.bind('<Button-3>', self.on_right_click)
        self.tree.bind("<ButtonPress-1>", self.b_down)
        self.tree.bind("<ButtonRelease-1>", self.b_up, add='+')
        self.tree.bind("<B1-Motion>", self.b_move, add='+')

    def b_down(self, event):
        if self.tree.identify_row(event.y) not in self.tree.selection():
            self.tree.selection_set(self.tree.identify_row(event.y))

    def b_up(self, event):
        if self.tree.identify_row(event.y) in self.tree.selection():
            self.tree.selection_set(self.tree.identify_row(event.y))
        if self.moved_flag:
            self.adjust_queue_turn()
            self.update()
            self.moved_flag = False

    def b_move(self, event):
        moveto = self.tree.index(self.tree.identify_row(event.y))
        if data_class.queue_running and (moveto == 0 or self.tree.index(self.tree.selection()) == 0):
            return
        for s in self.tree.selection():
            self.tree.move(s, '', moveto)
        self.moved_flag = True

    def do_pause_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        data_class.session.pause_process(name)

    def do_resume_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        data_class.session.resume_process(name)

    def do_kill_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        data_class.session.kill_process(name)

    def update(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for obj in data_class.projects_queue:
            data_class.my_list.insert(obj.get_list())
        self._column_sort("Turn", False)

    def adjust_queue_turn(self):
        turn = 0
        aux_list = []
        for listbox_entry in self.tree.get_children():
            for proj in data_class.projects_queue:
                if proj.name == self.tree.item(listbox_entry)['values'][0]:
                    if not proj.status == "Done":
                        turn += 1
                        heapq.heappush(aux_list, [int(turn), self.tree.item(listbox_entry)['values'][0]])
                        proj.turn = turn
        data_class.heap_queue = aux_list

    def on_right_click(self, event):
        if len(self.tree.identify('item', event.x, event.y)) > 0:
            self.popup_menu.post(event.x_root, event.y_root)
            self.mouse_event = event
        data_class.my_list.update()

    def insert(self, item):
        self.tree.insert('', 'end', values=item)

    def delete(self):
        element = self.tree.item(self.tree.selection())['values'][0]
        if self.element_running(element):
            self.remove_from_queue(element)
            self.adjust_queue_turn()
            self.update()
            self._column_sort("Turn", False)
        else:
            messagebox.showwarning("Warning", "You can't delete a project that is running!")

    def element_running(self, data):
        for obj in data_class.projects_queue:
            if obj.name == data:
                if obj.status == "Running":
                    return False
                else:
                    return True

    def remove_from_queue(self, data):
        aux_list = []
        # REMOVE FROM THE GUI
        self.tree.delete(self.tree.selection())

        # REMOVE FROM THE LIST OF PROJECT OBJECTS
        for obj in data_class.projects_queue:
            if obj.name == data:
                data_class.projects_queue.remove(obj)

        # REMOVE FROM THE ACTUAL QUEUE
        for element in data_class.heap_queue:
            if element[1] != data:
                heapq.heappush(aux_list, element)
        data_class.heap_queue = aux_list

    def _load_data(self):
        # configure column headings
        for c in self.dataCols:
            self.tree.heading(c, text=c.title())
                              # command=lambda c=c: self._column_sort(c, self.SortDir)
            self.tree.column(c, width=Font().measure(c.title()))

        # add data to the tree
        for item in data_class.data_table:
            self.tree.insert('', 'end', values=item)

            # and adjust column widths if necessary
            for idx, val in enumerate(item):
                iwidth = Font().measure(val)
                if self.tree.column(self.dataCols[idx], 'width') < iwidth:
                    self.tree.column(self.dataCols[idx], width=iwidth)

    def _column_sort(self, col, descending=False):
        # grab values to sort as a list of tuples (column value, column id)
        # e.g. [('Argentina', 'I001'), ('Australia', 'I002'), ('Brazil', 'I003')]
        col = "Turn"
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]

        # reorder data
        # tkinter looks after moving other items in
        # the same row
        data.sort(reverse=descending)
        for indx, item in enumerate(data):
            self.tree.move(item[1], '', indx)  # item[1] = item Identifier

        # reverse sort direction for next sort operation
        self.SortDir = not descending


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.connection_exist = False
        self.init_window()
        data_class.session = None
        self.cpu_number = 0

    def donothing(self):
        filewin = Toplevel(self.master)
        button = Button(filewin, text="Do nothing button")
        button.pack()

    def init_window(self):
        self.master.title("Queue")
        self.master.geometry("750x420")

        # Init MenuBar
        menubar = Menu(self.master)
        # create a pulldown menu, and add it to the menu bar
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Connect", command=self.connect)
        filemenu.add_command(label="Credentials", command=self.enter_credentials_widget)
        filemenu.add_command(label="Disconnect", command=self.disconnect)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="Settings", menu=filemenu)
        self.master.config(menu=menubar)

        # The content of the frame
        top_frame = Frame(self.master, width=750, height=120, pady=3)
        center_frame = Frame(self.master, bg='gray', width=750, height=200, padx=3, pady=3)
        bottom_frame = Frame(self.master, bg='forest green', width=750, height=60, padx=3, pady=3)
        top_frame.grid(row=0, sticky="ew")
        center_frame.grid(row=1, sticky="nsew")
        bottom_frame.grid(row=2, sticky="ew")
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        Label(top_frame, text="Queuer of Simulations",fg= "green", font=("Helvetica", 12)).grid(row=0, column=4)
        Label(top_frame, text="Host:").grid(row=1,column=1, sticky = E)
        data_class.iplabel = Label(top_frame, text=config.host)
        data_class.iplabel.grid(row=1, column=2, sticky = E)
        Label(top_frame, text="Connection Status:").grid(row=2,column=1, sticky = W)
        Label(top_frame, text="Queue Status:").grid(row=3,column=1, sticky = W)
        data_class.status_label = Label(top_frame, text="Disconnected", fg="red")
        data_class.status_queue_label = Label(top_frame, text="Stopped", fg="red")
        data_class.status_label.grid(row=2, column=2, sticky=E)
        data_class.status_queue_label.grid(row=3, column=2, sticky=E)
        Label(top_frame, text="CPU").grid(row=1, column=4, sticky=E)
        Label(top_frame, text="CPU 0:").grid(row=2, column=4, sticky=E)
        data_class.cpu_list.append(Label(top_frame, text="--"))
        data_class.cpu_list[0].grid(row=2, column=5, sticky=W)
        Label(top_frame, text="CPU 1:").grid(row=2, column=6, sticky=E)
        data_class.cpu_list.append(Label(top_frame, text="--"))
        data_class.cpu_list[1].grid(row=2, column=7, sticky=W)
        Label(top_frame, text="CPU 2:").grid(row=3, column=4, sticky=E)
        data_class.cpu_list.append(Label(top_frame, text="--"))
        data_class.cpu_list[2].grid(row=3, column=5, sticky=W)
        Label(top_frame, text="CPU 3:").grid(row=3, column=6, sticky=E)
        data_class.cpu_list.append(Label(top_frame, text="--"))
        data_class.cpu_list[3].grid(row=3, column=7, sticky=W)
        Label(top_frame, text="RAM").grid(row=1, column=8, sticky=W)
        Label(top_frame, text="total:").grid(row=2, column=8, sticky=E, padx=(10,0))
        data_class.ram_stats.append(Label(top_frame, text="--"))
        data_class.ram_stats[0].grid(row=2, column=9, sticky=W)
        Label(top_frame, text="used:").grid(row=3, column=8, sticky=E, padx=(10,0))
        data_class.ram_stats.append(Label(top_frame, text="--"))
        data_class.ram_stats[1].grid(row=3, column=9, sticky=W)
        Label(top_frame, text="free:").grid(row=2, column=10, sticky=E)
        data_class.ram_stats.append(Label(top_frame, text="--"))
        data_class.ram_stats[2].grid(row=2, column=11, sticky=W)
        Label(top_frame, text="usage:").grid(row=3, column=10, sticky=E)
        data_class.ram_stats.append(Label(top_frame, text="--"))
        data_class.ram_stats[3].grid(row=3, column=11, sticky=W)
        Label(top_frame, text="Disk").grid(row=1, column=12, sticky=W)
        Label(top_frame, text="total:").grid(row=2, column=12, sticky=E, padx=(10,0))
        data_class.disk_storage.append(Label(top_frame, text="--"))
        data_class.disk_storage[0].grid(row=2, column=13, sticky=W)
        Label(top_frame, text="used:").grid(row=3, column=12, sticky=E, padx=(10,0))
        data_class.disk_storage.append(Label(top_frame, text="--"))
        data_class.disk_storage[1].grid(row=3, column=13, sticky=W)
        Label(top_frame, text="free:").grid(row=2, column=14, sticky=E)
        data_class.disk_storage.append(Label(top_frame, text="--"))
        data_class.disk_storage[2].grid(row=2, column=15, sticky=W)
        Label(top_frame, text="usage:").grid(row=3, column=14, sticky=E)
        data_class.disk_storage.append(Label(top_frame, text="--"))
        data_class.disk_storage[3].grid(row=3, column=15, sticky=W)
        data_class.my_list = DDList(center_frame, height=10)
        Button(bottom_frame, text='Pause', command=self.donothing).pack(side=RIGHT, fill=Y, padx=(0,10))
        Button(bottom_frame, text='Resume', command=self.donothing).pack(side=RIGHT, fill=Y)
        Button(bottom_frame, text='Delete', command=data_class.my_list.delete).pack(side=RIGHT, fill=Y)
        Button(bottom_frame, text='Add', command=self.add_project).pack(side=LEFT,fill=Y, padx=(10,0))
        data_class.status_button = Button(bottom_frame, text='Start Queue', command=self.toggle_queue_status)
        data_class.status_button.pack(side=LEFT)
        Label(bottom_frame, text="Queue Mode: Regular", bg="forest green").pack(side=LEFT, fill=Y)

    def toggle_queue_status(self):
        if data_class.session.is_connected:
            if not data_class.queue_running:
                print(data_class.heap_queue)
                if len(data_class.heap_queue) == 0:
                    self.gen_projects_queue()
                data_class.queue_running = True
                data_class.status_button.config(text="Stop Queue")
                data_class.status_queue_label.config(text="Running", fg="green")
                threading.Thread(target=self.start_queue).start()
            else:
                data_class.queue_running = False
                data_class.status_button.config(text="Start Queue")
                data_class.status_queue_label.config(text="Stopped", fg="red")
        else:
            messagebox.showerror("Error", "Please connect before starting the queue.")

    def gen_projects_queue(self):
        for project in data_class.projects_queue:
            if project.status != "Done":
                heapq.heappush(data_class.heap_queue, [int(project.turn), project.name])

    def add_project(self):
        reload(config)
        if self.connection_exist:
            if True:
                targetpath = f"\\\\{config.host}\\Projects"
                filepath = filedialog.askopenfilename(parent=root, filetypes=(("Script Files", "*.SCRIPT"),
                                                                              ("All Files", "*.*")),
                                                      initialdir=targetpath,
                                                      title='Please select a .SCRIPT project')
                self.add_to_queue(filepath)
        else:
            messagebox.showerror("Error", "Please connect before adding to a queue.")

    def start_queue(self):
        while data_class.queue_running:
            print(data_class.heap_queue)
            if len(data_class.heap_queue) > 0:
                task = data_class.heap_queue[0]
            else:
                messagebox.showwarning("Warning", "Queue is empty!")
                self.toggle_queue_status()
                return
            for proj in data_class.projects_queue:
                if proj.name == task[1]:
                    if proj.status == "Running":
                        break
                    else:
                        proj.status = "Running"
                        data_class.my_list.update()
                        data_class.task_done = False
                        threading.Thread(target=data_class.session.start_project, args=(proj.bash_path, proj.name)).start()
                        break
            while True:
                if data_class.task_done:
                    proj.status = "Done"
                    proj.turn = None
                    heapq.heappop(data_class.heap_queue)
                    data_class.my_list.adjust_queue_turn()
                    try:
                        data_class.my_list.update()
                    except:
                        return
                    break


    def add_to_queue(self, filepath, icont=0):
        """
        Pops an filedialog window that will ask for the file wanted to be queued
        Then adds an element to the queue both graphical and the heapq"""

        with open(filepath, 'r') as doc:
            data = doc.read()
            cores = data[data.find("-t")+2]
            tofilename = filepath.split("/")[-1]
            filename = tofilename[:tofilename.find(".")]
            auxfilename = filename

        while self.is_repeated(filename):
            icont += 1
            filename = f"{auxfilename} ({icont})"

        new = ProjectSim(filename, filepath, cores, "Queued", self.count_queued_project(), datetime.now().strftime("%Y-%m-%d / %H:%M:%S"))
        new.bash_path = self.bashify(filepath)
        print(new.bash_path)
        heapq.heappush(data_class.heap_queue, [int(self.count_queued_project()), filename])
        data_class.projects_queue.append(new)
        data_class.my_list.insert(new.get_list())
        data_class.my_list.update()

    def count_queued_project(self):
        return len(data_class.heap_queue)+1

    def bashify(self, filepath):
        filepath = filepath.split("/")
        newfilepath = ""
        for i in range(len(filepath)-1, -1, -1):
            if i == len(filepath)-1:
                newfilepath = f"/{filepath[i]}"
            elif filepath[i].count(".") == 3:
                return newfilepath
            else:
                newfilepath = f"/{filepath[i]}" + newfilepath


    def is_repeated(self, data):
        for obj in data_class.projects_queue:
            if obj.name == data:
                return True
        return False

    def enter_credentials_widget(self):
        top = Toplevel()
        host = StringVar()
        user = StringVar()
        password = StringVar()

        top.title("Connect to machine")
        top.resizable(width=False, height=False)
        Label(top, text="Login Credentials", fg="green", font=("Helvetica", 12)).grid(row=0, column=1)

        host.set(config.host)
        user.set(config.user)
        password.set(base64.b64decode(config.password).decode())

        Label(top, text="IP").grid(row=1, pady=4)
        Label(top, text="User").grid(row=2)
        Label(top, text="Password").grid(row=3)

        e1 = Entry(top, textvariable=host)
        e2 = Entry(top, textvariable=user)
        e3 = Entry(top, textvariable=password)

        e3.config(show="*")

        e1.grid(row=1, column=1)
        e2.grid(row=2, column=1)
        e3.grid(row=3, column=1)

        button1 = Button(top, text="Cancel", command=top.destroy)
        button2 = Button(top, text="Connect", command=lambda: self.update_credentials(host.get(), user.get(), password.get(), top))
        button1.grid(row=4, column=1, sticky=E, pady=4)
        button2.grid(row=4, column=2, sticky=W, padx=2, pady=4)

    def update_credentials(self, host, user, password, top):
        # First update the credentials of the config file.
        if host.count('.') == 3:
            data_class.status_label.config(text="Connecting...", fg="orange")
            if not password == base64.b64decode(config.password).decode():
                encoded_password = base64.b64encode(password.encode())
            else:
                encoded_password = config.password
            with open("config.py", "w") as sf:
                sf.write(f"host = \"{host}\" \nuser = \"{user}\" \npassword = {encoded_password}")
            reload(config)
            if self.connection_exist:
                if data_class.session.is_connected:
                    self.disconnect()
            data_class.session = Session(config.host, config.user, base64.b64decode(config.password).decode())
            t = threading.Thread(target=self.connect_via_ssh)
            t.start()
            data_class.iplabel.config(text=host)
        else:
            messagebox.showerror("Error", "Invalid IP")
        top.destroy()

    def connect(self):
        if not self.connection_exist:
            data_class.status_label.config(text="Connecting...", fg="orange")
            os.system(f"net use x: \\\\{config.host}\\projects")
            data_class.session = Session(config.host, config.user, base64.b64decode(config.password).decode())
            self.connection_exist = True
            t = threading.Thread(target=self.connect_via_ssh)
            t.start()
        else:
            messagebox.showinfo("Connection", "You are already connected.")

    def set_null(self):
        for label in data_class.disk_storage:
            label.config(text="--")
        for label in data_class.ram_stats:
            label.config(text="--")
        for label in data_class.cpu_list:
            label.config(text="--")

    def disconnect(self):
        # STOP QUEUE
        data_class.queue_running = False
        data_class.status_button.config(text="Start Queue")
        data_class.status_queue_label.config(text="Stopped", fg="red")
        # SESSION OFF
        data_class.session.flag_stop = True
        data_class.status_label.config(text="Disconnected", fg="red")
        self.connection_exist = False
        data_class.session.ssh.close()
        self.set_null()

    def connect_via_ssh(self):
        if data_class.session.assert_connection():
            self.connection_exist = True
            data_class.status_label.config(text="Connected", fg="green")
            data_class.session.start_threads()
            self.cpu_number = data_class.session.get_cpu_num()
        else:
            self.disconnect()
            messagebox.showerror("Error", "Connection refused: check credentials and ip.")
            return

class Session(Window):
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
        threading.Thread(target=self.gen_ram_stats).start()
        threading.Thread(target=self.gen_disk_stats).start()

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

    def start_project(self, filepath, filename):
        path = filepath[1:filepath.rfind("/")]+"/"
        true_filename = filepath[filepath.rfind("/")+1:]
        print(f'./"{true_filename}"')
        print(path)
        stdin, stdout, stderr = self.ssh.exec_command(f'cd {path} && ./"{true_filename}" & echo "pid:"$! && wait && echo "Command was completed"', get_pty=True)
        for response in iter(stdout.readline, ""):
            print(str(response))
            if "pid" in response:
                data_class.name_pid[filename] = int(response.split(":")[1])
                data_class.session.get_mpid_byname(filename)

            elif "Command was completed" in response:
                print(f"Task terminada por {filename} ")
                data_class.task_done = True
                return

    def pause_process(self , name):
        print(f"NAME IT : {data_class.name_mpid}" )
        self.ssh.exec_command(f'kill -SIGTSTP {data_class.name_mpid[name]}')

    def resume_process(self, name):
        self.ssh.exec_command(f'kill -SIGCONT {data_class.name_mpid[name]}')

    def kill_process(self, name):
        self.ssh.exec_command(f'kill -SIGKILL {data_class.name_mpid[name]}')
        data_class.task_stopped = True

    def get_mpid_byname(self, name):
        print(f'ps -p {data_class.name_pid[name]} -o ppid')
        stdin, stdout, stderr = self.ssh.exec_command(f'ps -p {data_class.name_pid[name]} -o ppid', get_pty=True)
        for mpid in iter(stdout.readline, ""):
            print("THIS: "+ str(mpid))
            if not "PPID" in mpid:
                data_class.name_mpid[name] = int(mpid)

    def get_cpu_num(self):
        stdin, stdout, stderr = self.ssh.exec_command('grep -c ^processor /proc/cpuinfo', get_pty=True)
        for line in iter(stdout.readline, ""):
            line = int(line)
            self.cpu_number = line
            return line

    def gen_cpu_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('mpstat -P ALL 1', get_pty=True)
        self.is_connected = True
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            if len(line) > 1:
                if line[2].isdigit():
                    self.cpu_usage.append(line[3])
                    if int(line[2]) == self.cpu_number-1:
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
                data_class.ram_stats[0].config(text=line[1]+"MB")
                data_class.ram_stats[1].config(text=line[2]+"MB")
                data_class.ram_stats[2].config(text=line[3]+"MB")
                data_class.ram_stats[3].config(text=str(100*(int(line[2])/int(line[1])))[:5] +"%")

    def gen_disk_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('df -h /home && while sleep 5; do df -h /home; done', get_pty=True)
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            if len(line)> 1:
                if "G" in line[0]:
                    data_class.disk_storage[0].config(text=line[0])
                    data_class.disk_storage[1].config(text=line[1])
                    data_class.disk_storage[2].config(text=line[2])
                    data_class.disk_storage[3].config(text=line[3])
                elif "G" in line[1]:
                    data_class.disk_storage[0].config(text=line[1])
                    data_class.disk_storage[1].config(text=line[2])
                    data_class.disk_storage[2].config(text=line[3])
                    data_class.disk_storage[3].config(text=line[4])

    def update_gui_values(self, values):
        for x in range(self.cpu_number):
            data_class.cpu_list[x].config(text=values[x])

class GUIData():
    def __init__(self, user, host):
        self.user = user
        self.host = host
        self.cpu_list = []
        self.data_table = []
        self.heap_queue = []
        self.projects_queue = []
        self.name_pid = {}
        self.name_mpid = {}
        self.ram_stats = []
        self.disk_storage = []
        self.queue_running = False
        self.task_stopped = False

if __name__ == "__main__":
    data_class = GUIData(config.user, config.host)
    root = Tk()
    app = Window(root)
    root.mainloop()

