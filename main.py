import base64
import heapq
import os
import threading
import time
from datetime import datetime
from importlib import reload
from tkinter import *
from tkinter import messagebox, ttk, filedialog
from tkinter.font import Font
import pickle
from paramiko import SSHClient, AutoAddPolicy

import config
from ProjectManClass import ProjectSim


class DDList():
    """ A Tkinter listbox with drag'n'drop reordering of entries. """

    def __init__(self, master, **kw):
        self.SortDir = True
        f = ttk.Frame(master)
        f.pack(fill=BOTH, expand=True)
        self.dataCols = ('Project Name', 'Status', 'Cores', 'Turn', 'Added date/time')
        self.tree = ttk.Treeview(columns=self.dataCols,
                                 show='headings')
        self.mouse_event = None
        self.moved_flag = False
        ysb = ttk.Scrollbar(orient=VERTICAL, command=self.tree.yview)
        self.popup_menu = Menu(master, tearoff=0)
        self.popup_menu.add_command(label="Delete",
                                    command=lambda: self.delete(self.mouse_event))
        self.popup_menu.add_command(label="Stop/Save",
                                    command=lambda: self.do_stop_process(self.mouse_event))
        self.popup_menu.add_command(label="Force Stop",
                                    command=lambda: self.do_kill_process(self.mouse_event))
        # self.popup_menu.add_command(label="Pause",
        #                             command=lambda: self.do_pause_process(self.mouse_event))
        # self.popup_menu.add_command(label="Resume",
        #                             command=lambda: self.do_resume_process(self.mouse_event))
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
        if len(self.tree.selection()) > 0:
            data_class.delete_button.config(state="normal")
        else:
            data_class.delete_button.config(state="disabled")

    def b_move(self, event):
        moveto = self.tree.index(self.tree.identify_row(event.y))
        if data_class.queue_running and (moveto == 0 or self.tree.index(self.tree.selection()) == 0):
            return
        for s in self.tree.selection():
            self.tree.move(s, '', moveto)
        self.moved_flag = True

    def do_kill_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        data_class.session.kill_process(name)

    # def do_pause_process(self, event):
    #     item = self.tree.identify('item', event.x, event.y)
    #     name = self.tree.item(item)['values'][0]
    #     data_class.session.pause_process(name)
    #
    # def do_resume_process(self, event):
    #     item = self.tree.identify('item', event.x, event.y)
    #     name = self.tree.item(item)['values'][0]
    #     data_class.session.resume_process(name)

    def do_stop_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        for obj in data_class.projects_queue:
            if obj.name == name:
                if obj.status == "Running":
                    path = obj.bash_path
                    obj.status = "Stopping"
                    data_class.my_list.update()
                else:
                    return
        data_class.session.stop_process(path)

    def update(self, refill = True):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if refill:
            for obj in data_class.projects_queue:
                data_class.my_list.insert(obj.get_list())
            self._column_sort("Turn", False)
        if not len(data_class.heap_queue) > 0:
            data_class.status_button.config(state="disabled")
        else:
            data_class.status_button.config(state="normal")

    def project_running(self):
        is_running = False
        for listbox_entry in self.tree.get_children():
            for proj in data_class.projects_queue:
                if proj.name == self.tree.item(listbox_entry)['values'][0]:
                    if proj.status == "Running":
                        is_running = True
        return is_running

    def adjust_queue_turn(self):
        turn = 0
        aux_list = []
        for listbox_entry in self.tree.get_children():
            for proj in data_class.projects_queue:
                if proj.name == self.tree.item(listbox_entry)['values'][0]:
                    if proj.status == "Running" or proj.status == "Queued":
                        turn += 1
                        heapq.heappush(aux_list, [int(turn), self.tree.item(listbox_entry)['values'][0]])
                        proj.turn = turn
        data_class.heap_queue = aux_list

    def on_right_click(self, event):
        if len(self.tree.identify('item', event.x, event.y)) > 0:
            if not self.element_running(self.tree.item(self.tree.identify('item', event.x, event.y))['values'][0]):
                self.popup_menu.entryconfig(1, state="disabled")
                self.popup_menu.entryconfig(2, state="disabled")
            else:
                self.popup_menu.entryconfig(0, state="disabled")
                self.popup_menu.entryconfig(1, state="normal")
                self.popup_menu.entryconfig(2, state="normal")
            self.popup_menu.post(event.x_root, event.y_root)
            self.mouse_event = event

    def insert(self, item):
        self.tree.insert('', 'end', values=item)

    def delete(self, event = None):
        if event:
            item = self.tree.identify('item', event.x, event.y)
            element = self.tree.item(item)['values'][0]
        else:
            item = self.tree.selection()
            element = self.tree.item(item)['values'][0]
        if not self.element_running(element):
            self.remove_from_queue(element, item)
            self.adjust_queue_turn()
            self.update()
            self._column_sort("Turn", False)
        else:
            messagebox.showwarning("Warning", "You can't delete a project that is running!")
        data_class.delete_button.config(state="disabled")

    def element_running(self, data):
        for obj in data_class.projects_queue:
            if obj.name == data:
                if obj.status == "Running":
                    return True
                else:
                    return False

    def remove_from_queue(self, data, item):
        aux_list = []
        self.tree.delete(item)

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
        data_class.connection_exist = False
        data_class.session = None
        self.master.withdraw()
        self.enter_credentials_widget()
        self.init_window()
        self.cpu_number = 0
        self.queue_thread = threading.Thread()

    def ask_exit(self):
        result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
        if result == 'yes':
            root.quit()
        else:
            return

    def ask_disconnection(self):
        result = messagebox.askquestion("Disconnect", "Are  you sure you want to disconnect?", icon='warning')
        if result == 'yes':
            self.new_connection()
        else:
            return

    def new_connection(self):
        self.disconnect()
        self.master.withdraw()
        self.enter_credentials_widget()

    def init_window(self):
        self.master.title("SimQ")
        self.master.geometry("830x360")

        # Init MenuBar
        data_class.menu_connection = Menu(self.master)

        # create a pulldown menu, and add it to the menu bar
        connect_menu = Menu(data_class.menu_connection, tearoff=0)
        setting_menu = Menu(data_class.menu_connection, tearoff=0)

        Item0 = IntVar()
        setting_menu.add_command(label='Auto queueing', command= self.save_action)
        # connect_menu.add_separator()
        data_class.menu_connection.add_cascade(label="Disconnect", command=self.ask_disconnection)
        data_class.menu_connection.add_cascade(label="Settings", menu=setting_menu)
        data_class.menu_connection.add_cascade(label="Exit", command=self.ask_exit)

        self.master.config(menu=data_class.menu_connection)
        self.master.pack_propagate(0)

        # The content of the frame
        title_frame = Frame(self.master, width=830,bg="#D8D8D8", height=40)
        top_frame = Frame(self.master, width=830, height=80)
        center_frame = Frame(self.master, bg='gray', width=830, height=200, padx=3, pady=3)
        bottom_frame = Frame(self.master, bg='#0B6623', width=830, height=60, padx=3, pady=3)
        title_frame.grid(row=0, sticky ="ew")
        top_frame.grid(row=1, sticky="ew", pady=3)
        center_frame.grid(row=2, sticky="nsew")
        bottom_frame.grid(row=3, sticky="ew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        ##Top Frame Frames
        connection_frame = Frame(top_frame,width = 260, height = 90)
        cpu_frame = Frame(top_frame,width = 180, height = 70, borderwidth = 1, relief=RIDGE)
        ram_frame = Frame(top_frame,width = 215, height = 70, borderwidth = 1, relief=RIDGE)
        disk_frame = Frame(top_frame,width = 175, height = 70, borderwidth = 1, relief=RIDGE)
        connection_frame.grid(row=0, column=0, sticky="ew")
        cpu_frame.grid(row=0, column=1, sticky="nsew", padx=(50,0))
        ram_frame.grid(row=0 , column=2, sticky="nsew",padx=(10,0))
        disk_frame.grid(row=0, column=3, sticky="nsew",padx=(10,0))
        Label(title_frame, text="SimQ", bg="#D8D8D8", fg="green", font=("Helvetica", 14, "bold")).pack()
        Label(connection_frame, text="Host:").grid(row=0, column=0, sticky=E)
        data_class.iplabel = Label(connection_frame, text=config.host)
        data_class.iplabel.grid(row=0, column=1, sticky=E)
        Label(connection_frame, text="Connection Status:").grid(row=1, column=0, sticky=W)
        Label(connection_frame, text="Queue Status:").grid(row=2, column=0, sticky=W)
        data_class.status_label = Label(connection_frame, text="Disconnected", fg="red")
        data_class.status_queue_label = Label(connection_frame, text="Stopped", fg="red")
        data_class.status_label.grid(row=1, column=1, sticky=E)
        data_class.status_queue_label.grid(row=2, column=1, sticky=E)
        Label(cpu_frame, text="CPU", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(cpu_frame, text="CPU 0:").grid(row=1, column=0, sticky=E)
        data_class.cpu_list.append(Label(cpu_frame, text="--"))
        data_class.cpu_list[0].grid(row=1, column=1, sticky=W)
        Label(cpu_frame, text="CPU 1:").grid(row=2, column=0, sticky=E)
        data_class.cpu_list.append(Label(cpu_frame, text="--"))
        data_class.cpu_list[1].grid(row=2, column=1, sticky=W)
        Label(cpu_frame, text="CPU 2:").grid(row=1, column=2, sticky=E)
        data_class.cpu_list.append(Label(cpu_frame, text="--"))
        data_class.cpu_list[2].grid(row=1, column=3, sticky=W)
        Label(cpu_frame, text="CPU 3:").grid(row=2, column=2, sticky=E)
        data_class.cpu_list.append(Label(cpu_frame, text="--"))
        data_class.cpu_list[3].grid(row=2, column=3, sticky=W)
        Label(ram_frame, text="RAM", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(ram_frame, text="total:").grid(row=1, column=0, sticky=E, padx=(10, 0))
        data_class.ram_stats.append(Label(ram_frame, text="--"))
        data_class.ram_stats[0].grid(row=1, column=1, sticky=W)
        Label(ram_frame, text="used:").grid(row=2, column=0, sticky=E, padx=(10, 0))
        data_class.ram_stats.append(Label(ram_frame, text="--"))
        data_class.ram_stats[1].grid(row=2, column=1, sticky=W)
        Label(ram_frame, text="free:").grid(row=1, column=2, sticky=E)
        data_class.ram_stats.append(Label(ram_frame, text="--"))
        data_class.ram_stats[2].grid(row=1, column=3, sticky=W)
        Label(ram_frame, text="usage:").grid(row=2, column=2, sticky=E)
        data_class.ram_stats.append(Label(ram_frame, text="--"))
        data_class.ram_stats[3].grid(row=2, column=3, sticky=W)
        Label(disk_frame, text="Disk", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(disk_frame, text="total:").grid(row=1, column=0, sticky=E, padx=(10, 0))
        data_class.disk_storage.append(Label(disk_frame, text="--"))
        data_class.disk_storage[0].grid(row=1, column=1, sticky=W)
        Label(disk_frame, text="used:").grid(row=2, column=0, sticky=E, padx=(10, 0))
        data_class.disk_storage.append(Label(disk_frame, text="--"))
        data_class.disk_storage[1].grid(row=2, column=1, sticky=W)
        Label(disk_frame, text="free:").grid(row=1, column=2, sticky=E)
        data_class.disk_storage.append(Label(disk_frame, text="--"))
        data_class.disk_storage[2].grid(row=1, column=3, sticky=W)
        Label(disk_frame, text="usage:").grid(row=2, column=2, sticky=E)
        data_class.disk_storage.append(Label(disk_frame, text="--"))
        data_class.disk_storage[3].grid(row=2, column=3, sticky=W)
        data_class.my_list = DDList(center_frame, height=6)
        # Defining buttons
        data_class.delete_button = Button(bottom_frame, text='Delete',state="disabled", command=data_class.my_list.delete)
        data_class.delete_button.pack(side=RIGHT, fill=BOTH, padx=(5, 10))
        Button(bottom_frame, text='Add', command=self.add_project).pack(side=RIGHT, fill=Y , padx=(10, 0))
        data_class.status_button = Button(bottom_frame, text='Start Queue', command=self.toggle_queue_status)
        data_class.status_button.pack(side=LEFT, padx=(10, 0))

        # Config of frames
        title_frame.grid_propagate(False)
        cpu_frame.grid_propagate(False)
        ram_frame.grid_propagate(False)
        disk_frame.grid_propagate(False)

    def toggle_queue_status(self):
        if not data_class.queue_running:
            print(data_class.heap_queue)
            data_class.queue_running = True
            data_class.status_button.config(text="Stop Queue")
            data_class.status_queue_label.config(text="Running", fg="green")
            if not self.queue_thread.isAlive():
                self.queue_thread = threading.Thread(target=self.start_queue)
                self.queue_thread.start()
        else:
            data_class.queue_running = False
            data_class.status_button.config(text="Start Queue")
            data_class.status_queue_label.config(text="Stopped", fg="red")


    def save_action(self):
        pass

    def add_project(self):
        reload(config)
        targetpath = f"\\\\{config.host}\\Projects"
        filepath = filedialog.askopenfilename(parent=root, filetypes=(("Script Files", "*.SCRIPT"),
                                                                      ("All Files", "*.*")),
                                              initialdir=targetpath,
                                              title='Please select a .SCRIPT project')
        if len(filepath) > 0:
            self.add_to_queue(filepath)

    def start_queue(self):
        while data_class.queue_running:
            print(data_class.heap_queue)
            if len(data_class.heap_queue) > 0:
                task = data_class.heap_queue[0]
            else:
                messagebox.showwarning("Queue finished", "The queue has finished!")
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
                        data_class.task_stopped = False
                        data_class.task_canceled = False
                        data_class.task_denied = False
                        threading.Thread(target=data_class.session.start_project,
                                         args=(proj.bash_path, proj.name)).start()
                        break
            while True:
                if data_class.task_done:
                    if data_class.task_stopped:
                        proj.status = "Stopped Gently"
                    elif data_class.task_canceled:
                        proj.status= "Stop Forced"
                    elif data_class.task_denied:
                        proj.status = "Permission Denied"
                    else:
                        proj.status = "Completed"
                    proj.turn = None
                    del data_class.name_pid[proj.name]
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
            cores = data[data.find("-t") + 2]
            tofilename = filepath.split("/")[-1]
            filename = tofilename[:tofilename.find(".")]
            auxfilename = filename

        while self.is_repeated(filename):
            icont += 1
            filename = f"{auxfilename} ({icont})"

        new = ProjectSim(filename, filepath, cores, "Queued", self.count_queued_project(),
                         datetime.now().strftime("%Y-%m-%d / %H:%M:%S"))
        new.bash_path = self.bashify(filepath)
        print(new.bash_path)
        heapq.heappush(data_class.heap_queue, [int(self.count_queued_project()), filename])
        data_class.projects_queue.append(new)
        data_class.my_list.insert(new.get_list())
        data_class.my_list.update()

    def count_queued_project(self):
        return len(data_class.heap_queue) + 1

    def bashify(self, filepath):
        filepath = filepath.split("/")
        newfilepath = ""
        for i in range(len(filepath) - 1, -1, -1):
            if i == len(filepath) - 1:
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
        self.top = Toplevel()
        self.top.geometry("400x400")
        data_class.progress = ttk.Progressbar(self.top, length=100, value=0)
        host = StringVar()
        user = StringVar()
        password = StringVar()

        self.top.title("Connect to machine")
        self.top.resizable(width=False, height=False)
        Label(self.top, text="Login Credentials", fg="green", font=("Helvetica", 10, "bold")).grid(row=0, column=1)

        host.set(config.host)
        user.set(config.user)
        password.set(base64.b64decode(config.password).decode())

        Label(self.top, text="IP").grid(row=1, pady=4)
        Label(self.top, text="User").grid(row=2)
        Label(self.top, text="Password").grid(row=3)

        e1 = Entry(self.top, textvariable=host)
        e2 = Entry(self.top, textvariable=user)
        e3 = Entry(self.top, textvariable=password)

        e3.config(show="*")

        e1.grid(row=1, column=1)
        e2.grid(row=2, column=1)
        e3.grid(row=3, column=1)
        data_class.progress.grid(row=6,column=1, sticky="NSEW")
        data_class.progress.grid_remove()

        button1 = Button(self.top, text="Quit", command=quit)
        data_class.button2 = Button(self.top, text="Connect",
                         command=lambda: self.update_credentials(host.get(), user.get(), password.get(), self.top))
        button1.grid(row=4, column=1, sticky=E, pady=4)
        data_class.button2.grid(row=4, column=2, sticky=W, padx=2, pady=4)

    def update_credentials(self, host, user, password, top):
        # First update the credentials of the config file.
        data_class.button2.config(state="disabled")
        if password == "" or user == "" or host == "":
            messagebox.showerror("Error", "Fill all the entry fields.")
            return
        if host.count('.') == 3:
            data_class.status_label.config(text="Connecting...", fg="orange")
            if not password == base64.b64decode(config.password).decode():
                encoded_password = base64.b64encode(password.encode())
            else:
                encoded_password = config.password
            with open("config.py", "w") as sf:
                sf.write(f"host = \"{host}\" \nuser = \"{user}\" \npassword = {encoded_password}")
            reload(config)
            if data_class.connection_exist:
                if data_class.session.is_connected:
                    self.disconnect()
            data_class.progress.grid()
            data_class.session = Session(config.host, config.user, base64.b64decode(config.password).decode())
            data_class.host = config.host
            data_class.progress.step(30)
            t = threading.Thread(target=self.connect_via_ssh)
            t.start()
            data_class.iplabel.config(text=host)
        else:
            messagebox.showerror("Error", "Invalid IP")
            data_class.progress.grid_remove()
            data_class.button2.config(state="normal")

    def set_null(self):
        for label in data_class.disk_storage:
            label.config(text="--")
        for label in data_class.ram_stats:
            label.config(text="--")
        for label in data_class.cpu_list:
            label.config(text="--")

    def pickle_session(self):
        if not data_class.queue_running and not data_class.my_list.project_running():
            try:
                with open("object.pickle", "rb") as r:
                    stored_data = pickle.load(r)
            except:
                stored_data = []
            saved = False
            for session_saved in stored_data:
                if session_saved[0] == data_class.host:
                    session_saved[1] = data_class.heap_queue
                    session_saved[2] = data_class.projects_queue
                    session_saved[3] = data_class.data_table
                    saved = True
            if not saved:
                stored_data.append(
                    [data_class.host, data_class.heap_queue, data_class.projects_queue, data_class.data_table])
            with open("object.pickle", "wb") as w:
                pickle.dump(stored_data, w)
        elif data_class.queue_running:
            messagebox.showwarning("Warning", "Stop the queue before disconnecting.")
        else:
            messagebox.showwarning("Warning", "Wait for project to stop running disconnecting.")

    def disconnect(self):
        # STOP QUEUE
        self.pickle_session()
        data_class.queue_running = False
        data_class.status_button.config(text="Start Queue")
        data_class.status_queue_label.config(text="Stopped", fg="red")
        # SESSION OFF
        data_class.session.flag_stop = True
        data_class.status_label.config(text="Disconnected", fg="red")
        data_class.connection_exist = False
        data_class.session.ssh.close()
        self.UI_disconnected()
        self.set_null()

    def UI_disconnected(self):
        data_class.heap_queue = []
        data_class.projects_queue = []
        data_class.data_table = []
        data_class.my_list.update(False)

    def depickle_session(self):
        try:
            with open("object.pickle", "rb") as f:
                stored_data = pickle.load(f)
                for saved_session in stored_data:
                    if data_class.host == saved_session[0]:
                        data_class.heap_queue = saved_session[1]
                        data_class.projects_queue = saved_session[2]
                        data_class.data_table = saved_session[3]
        except:
            pass
        data_class.progress.step(9.99)
        data_class.my_list.update()

    def connect_via_ssh(self):
        if data_class.session.assert_connection():
            data_class.progress.step(30)
            data_class.connection_exist = True
            data_class.status_label.config(text="Connected", fg="green")
            data_class.session.start_threads()
            self.cpu_number = data_class.session.get_cpu_num()
            data_class.button2.config(state="normal")
            self.depickle_session()
            self.top.destroy()
            self.master.deiconify()
            
        else:
            self.disconnect()
            messagebox.showerror("Error", "Connection refused: check credentials and ip.")
            data_class.progress.grid_remove()
            data_class.button2.config(state="normal")
            data_class.progress.config(value=0)
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
        data_class.progress.step(10)
        threading.Thread(target=self.gen_ram_stats).start()
        data_class.progress.step(10)
        threading.Thread(target=self.gen_disk_stats).start()
        data_class.progress.step(10)

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

    def start_project(self, filepath, filename, no_pid = True, fix_permissions = True):
        path = filepath[1:filepath.rfind("/")] + "/"
        true_filename = filepath[filepath.rfind("/") + 1:]
        stdin, stdout, stderr = self.ssh.exec_command(
            f'cd {path} && ./"{true_filename}" & echo "pid:"$! && wait && echo "Command was completed"', get_pty=True)
        for response in iter(stdout.readline, ""):
            print(response)
            if no_pid:
                if "pid" in response:
                    data_class.name_pid[filename] = int(response.split(":")[1])
                    print(data_class.name_pid[filename])
                    no_pid = False
            if fix_permissions:
                if "Permission denied" in response:
                    self.ssh.exec_command(F"cd {path} && chmod +x '{true_filename}'")
                    self.start_project(filepath, filename, False, False)
                    if not data_class.task_done:
                        data_class.task_denied = True
                    return
            if "Command was completed" in response:
                print(f'Task \"{filename}\" terminada por')
                data_class.task_done = True
                return

    # def pause_process(self, name):
    #     self.ssh.exec_command(f'kill -SIGTSTP {data_class.name_mpid[name]}')

    # def resume_process(self, name):
    #     self.ssh.exec_command(f'kill -SIGCONT {data_class.name_mpid[name]}')

    def stop_process(self, path):
        path = "."+path[:path.rfind('/')+1]
        self.ssh.exec_command(f'cd {path} && touch FDSTOP')
        data_class.task_stopped = True

    def get_mpid_byname(self, name):
        print(f'ps -p {data_class.name_pid[name]} -o ppid')
        stdin, stdout, stderr = self.ssh.exec_command(f'pgrep mpid', get_pty=True)
        for mpid in iter(stdout.readline, ""):
            print("THIS IS MPID:" + str(mpid))
            data_class.name_mpid[name] = int(mpid)
            data_class.has_mpid = True

    def get_cpu_num(self):
        stdin, stdout, stderr = self.ssh.exec_command('grep -c ^processor /proc/cpuinfo', get_pty=True)
        for line in iter(stdout.readline, ""):
            line = int(line)
            self.cpu_number = line
            return line

    def kill_process(self, name):
        self.ssh.exec_command(f'kill -SIGKILL {data_class.name_pid[name]}')
        data_class.task_canceled = True

    def gen_cpu_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('mpstat -P ALL 1', get_pty=True)
        self.is_connected = True
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            if len(line) > 1:
                if line[2].isdigit():
                    self.cpu_usage.append(str(round(float(line[3])))+ "%")
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
                data_class.ram_stats[0].config(text=line[1] + "MB")
                data_class.ram_stats[1].config(text=line[2] + "MB")
                data_class.ram_stats[2].config(text=line[3] + "MB")
                data_class.ram_stats[3].config(text=str(100 * (int(line[2]) / int(line[1])))[:5] + "%")

    def gen_disk_stats(self):
        stdin, stdout, stderr = self.ssh.exec_command('df -h /home && while sleep 5; do df -h /home; done',
                                                      get_pty=True)
        for line in iter(stdout.readline, ""):
            if self.flag_stop:
                break
            line = line.split()
            if len(line) > 1:
                if "G" in line[0]:
                    data_class.disk_storage[0].config(text=line[0] + "B")
                    data_class.disk_storage[1].config(text=line[1] + "B")
                    data_class.disk_storage[2].config(text=line[2] + "B")
                    data_class.disk_storage[3].config(text=line[3])
                elif "G" in line[1]:
                    data_class.disk_storage[0].config(text=line[1] + "B")
                    data_class.disk_storage[1].config(text=line[2] + "B")
                    data_class.disk_storage[2].config(text=line[3] + "B")
                    data_class.disk_storage[3].config(text=line[4])

    def update_gui_values(self, values):
        for x in range(self.cpu_number):
            data_class.cpu_list[x].config(text=values[x])


class GUIData:
    def __init__(self, user, host):
        self.user = user
        self.host = host
        self.load = False
        self.connection_exist = False
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
        self.task_canceled = False


def on_closing():
    result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
    if result == 'yes':
        pass
    else:
        return
    if not data_class.queue_running and not data_class.my_list.project_running():
        with open("object.pickle", "rb") as r:
            stored_data = pickle.load(r)
        saved = False
        for session_saved in stored_data:
            if session_saved[0] == data_class.host:
                session_saved[1] = data_class.heap_queue
                session_saved[2] = data_class.projects_queue
                session_saved[3] = data_class.data_table
                saved = True
        if not saved:
            stored_data.append([data_class.host, data_class.heap_queue, data_class.projects_queue, data_class.data_table])
        with open("object.pickle", "wb") as w:
            pickle.dump(stored_data, w)
        if data_class.connection_exist:
            data_class.session.ssh.close()
        exit()
    elif data_class.queue_running:
        messagebox.showwarning("Warning", "Stop the queue before exiting the program.")
    else:
        messagebox.showwarning("Warning", "Wait for project to stop running before exiting.")


if __name__ == "__main__":
    data_class = GUIData(config.user, config.host)
    root = Tk()
    app = Window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
