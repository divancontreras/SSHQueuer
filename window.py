# External Imports
import base64
import heapq
import threading
from datetime import datetime
from importlib import reload
from tkinter import *
from tkinter.ttk import *
from tkinter import ttk, filedialog, Frame, Label, messagebox
import pickle
# Local Imports
import main
import listbox
import session
import config
from auxiliary_classes import Project


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self ,master)
        self.master = master
        main.global_data.connection_exist = False
        main.global_data.session = None
        self.master.withdraw()
        self.enter_credentials_widget()
        self.init_window()
        self.cpu_number = 0
        self.queue_thread = threading.Thread()

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
        main.global_data.menu_connection = Menu(self.master)

        # create a pulldown menu, and add it to the menu bar
        Menu(main.global_data.menu_connection, tearoff=0)
        setting_menu = Menu(main.global_data.menu_connection, tearoff=0)
        setting_menu.add_command(label='Auto queueing', command=self.save_action)
        # connect_menu.add_separator()
        main.global_data.menu_connection.add_cascade(label="Disconnect", command=self.ask_disconnection)
        main.global_data.menu_connection.add_cascade(label="Settings", menu=setting_menu)
        main.global_data.menu_connection.add_cascade(label="Exit", command=self.ask_exit)

        self.master.config(menu=main.global_data.menu_connection)
        self.master.pack_propagate(0)

        # The content of the frame
        title_frame = Frame(self.master, width=830, background="#D8D8D8", height=40)
        top_frame = Frame(self.master, width=830, height=80)
        center_frame = Frame(self.master, background='gray', width=830, height=200, padx=3, pady=3)
        bottom_frame = Frame(self.master, background='#0B6623', width=830, height=60, padx=3, pady=3)
        title_frame.grid(row=0, sticky="ew")
        top_frame.grid(row=1, sticky="ew", pady=3)
        center_frame.grid(row=2, sticky="nsew")
        bottom_frame.grid(row=3, sticky="ew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        # Top Frame Frames
        connection_frame = Frame(top_frame, width=260, height=90)
        cpu_frame = Frame(top_frame, width=180, height=70, borderwidth=1, relief=RIDGE)
        ram_frame = Frame(top_frame, width=215, height=70, borderwidth=1, relief=RIDGE)
        disk_frame = Frame(top_frame, width=175, height=70, borderwidth=1, relief=RIDGE)
        connection_frame.grid(row=0, column=0, sticky="ew")
        cpu_frame.grid(row=0, column=1, sticky="nsew", padx=(50, 0))
        ram_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        disk_frame.grid(row=0, column=3, sticky="nsew", padx=(10, 0))
        Label(title_frame, text="SimQ", background="#D8D8D8", foreground="green", font=("Helvetica", 14, "bold")).pack()
        Label(connection_frame, text="Host:").grid(row=0, column=0, sticky=E)
        main.global_data.iplabel = Label(connection_frame, text=config.host)
        main.global_data.iplabel.grid(row=0, column=1, sticky=E)
        Label(connection_frame, text="Connection Status:").grid(row=1, column=0, sticky=W)
        Label(connection_frame, text="Queue Status:").grid(row=2, column=0, sticky=W)
        main.global_data.status_label = Label(connection_frame, text="Disconnected", foreground="red")
        main.global_data.status_queue_label = Label(connection_frame, text="Stopped", foreground="red")
        main.global_data.status_label.grid(row=1, column=1, sticky=E)
        main.global_data.status_queue_label.grid(row=2, column=1, sticky=E)
        Label(cpu_frame, text="CPU", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(cpu_frame, text="CPU 0:").grid(row=1, column=0, sticky=E)
        main.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        main.global_data.cpu_list[0].grid(row=1, column=1, sticky=W)
        Label(cpu_frame, text="CPU 1:").grid(row=2, column=0, sticky=E)
        main.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        main.global_data.cpu_list[1].grid(row=2, column=1, sticky=W)
        Label(cpu_frame, text="CPU 2:").grid(row=1, column=2, sticky=E)
        main.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        main.global_data.cpu_list[2].grid(row=1, column=3, sticky=W)
        Label(cpu_frame, text="CPU 3:").grid(row=2, column=2, sticky=E)
        main.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        main.global_data.cpu_list[3].grid(row=2, column=3, sticky=W)
        Label(ram_frame, text="RAM", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(ram_frame, text="total:").grid(row=1, column=0, sticky=E, padx=(10, 0))
        main.global_data.ram_stats.append(Label(ram_frame, text="--"))
        main.global_data.ram_stats[0].grid(row=1, column=1, sticky=W)
        Label(ram_frame, text="used:").grid(row=2, column=0, sticky=E, padx=(10, 0))
        main.global_data.ram_stats.append(Label(ram_frame, text="--"))
        main.global_data.ram_stats[1].grid(row=2, column=1, sticky=W)
        Label(ram_frame, text="free:").grid(row=1, column=2, sticky=E)
        main.global_data.ram_stats.append(Label(ram_frame, text="--"))
        main.global_data.ram_stats[2].grid(row=1, column=3, sticky=W)
        Label(ram_frame, text="usage:").grid(row=2, column=2, sticky=E)
        main.global_data.ram_stats.append(Label(ram_frame, text="--"))
        main.global_data.ram_stats[3].grid(row=2, column=3, sticky=W)
        Label(disk_frame, text="Disk", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(disk_frame, text="total:").grid(row=1, column=0, sticky=E, padx=(10, 0))
        main.global_data.disk_storage.append(Label(disk_frame, text="--"))
        main.global_data.disk_storage[0].grid(row=1, column=1, sticky=W)
        Label(disk_frame, text="used:").grid(row=2, column=0, sticky=E, padx=(10, 0))
        main.global_data.disk_storage.append(Label(disk_frame, text="--"))
        main.global_data.disk_storage[1].grid(row=2, column=1, sticky=W)
        Label(disk_frame, text="free:").grid(row=1, column=2, sticky=E)
        main.global_data.disk_storage.append(Label(disk_frame, text="--"))
        main.global_data.disk_storage[2].grid(row=1, column=3, sticky=W)
        Label(disk_frame, text="usage:").grid(row=2, column=2, sticky=E)
        main.global_data.disk_storage.append(Label(disk_frame, text="--"))
        main.global_data.disk_storage[3].grid(row=2, column=3, sticky=W)
        main.global_data.my_list = listbox.DDList(center_frame, height=6)
        # Defining buttons
        main.global_data.delete_button = ttk.Button(bottom_frame, text='Delete', state="disabled",
                                               command=main.global_data.my_list.delete)
        main.global_data.delete_button.pack(side=RIGHT, fill=BOTH, padx=(5, 10))
        Button(bottom_frame, text='Add', command=self.add_project).pack(side=RIGHT, fill=Y, padx=(10, 0))
        main.global_data.status_button = Button(bottom_frame, text='Start Queue', command=self.toggle_queue_status)
        main.global_data.status_button.pack(side=LEFT, padx=(10, 0))

        # Config of frames
        title_frame.grid_propagate(False)
        cpu_frame.grid_propagate(False)
        ram_frame.grid_propagate(False)
        disk_frame.grid_propagate(False)

    def toggle_queue_status(self):
        if not main.global_data.queue_running:
            print(main.global_data.heap_queue)
            main.global_data.queue_running = True
            main.global_data.status_button.config(text="Stop Queue")
            main.global_data.status_queue_label.config(text="Running", foreground="green")
            if not self.queue_thread.isAlive():
                self.queue_thread = threading.Thread(target=self.start_queue)
                self.queue_thread.start()
        else:
            main.global_data.queue_running = False
            main.global_data.status_button.config(text="Start Queue")
            main.global_data.status_queue_label.config(text="Stopped", foreground="red")

    def save_action(self):
        pass

    def add_project(self):
        reload(config)
        targetpath = f"\\\\{config.host}\\Projects"
        filepath = filedialog.askopenfilename(parent=main.root, filetypes=(("Script Files", "*.SCRIPT"),
                                                                      ("All Files", "*.*")),
                                              initialdir=targetpath,
                                              title='Please select a .SCRIPT project')
        if len(filepath) > 0:
            self.add_to_queue(filepath)

    def start_queue(self):
        while main.global_data.queue_running:
            print(main.global_data.heap_queue)
            if len(main.global_data.heap_queue) > 0:
                task = main.global_data.heap_queue[0]
            else:
                messagebox.showwarning("Queue finished", "The queue has finished!")
                self.toggle_queue_status()
                return
            for proj in main.global_data.projects_queue:
                if proj.name == task[1]:
                    if proj.status == "Running":
                        break
                    else:
                        proj.status = "Running"
                        main.global_data.my_list.update()
                        main.global_data.task_done = False
                        main.global_data.task_stopped = False
                        main.global_data.task_canceled = False
                        main.global_data.task_denied = False
                        threading.Thread(target=main.global_data.session.start_project,
                                         args=(proj.bash_path, proj.name)).start()
                        break
            while True:
                if main.global_data.task_done:
                    if main.global_data.task_stopped:
                        proj.status = "Stopped Gently"
                    elif main.global_data.task_canceled:
                        proj.status = "Stop Forced"
                    elif main.global_data.task_denied:
                        proj.status = "Permission Denied"
                    else:
                        proj.status = "Completed"
                    proj.turn = None
                    del main.global_data.name_pid[proj.name]
                    heapq.heappop(main.global_data.heap_queue)
                    main.global_data.my_list.adjust_queue_turn()
                    try:
                        main.global_data.my_list.update()
                    except ReferenceError:
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

        new = Project(filename, filepath, cores, "Queued", self.count_queued_project(),
                      datetime.now().strftime("%Y-%m-%d / %H:%M:%S"))
        new.bash_path = self.bashify(filepath)
        print(new.bash_path)
        heapq.heappush(main.global_data.heap_queue, [int(self.count_queued_project()), filename])
        main.global_data.projects_queue.append(new)
        main.global_data.my_list.insert(new.get_list())
        main.global_data.my_list.update()

    def enter_credentials_widget(self):
        self.top = Toplevel(self.master)
        self.top.geometry("400x400")

        main.global_data.progress = ttk.Progressbar(self.top, length=100, value=0)
        host = StringVar()
        user = StringVar()
        password = StringVar()

        self.top.title("Connect to machine")
        self.top.resizable(width=False, height=False)
        Label(self.top, text="Login Credentials", foreground="green", font=("Helvetica", 10, "bold")).grid(row=0, column=1)

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
        main.global_data.progress.grid(row=6, column=1, sticky="NSEW")
        main.global_data.progress.grid_remove()

        button1 = ttk.Button(self.top, text="Quit", command=quit)
        main.global_data.button2 = ttk.Button(self.top, text="Connect",
                                         command=lambda: self.update_credentials(host.get(),
                                                                                 user.get(),
                                                                                 password.get()))
        button1.grid(row=4, column=1, sticky=E, pady=4)
        main.global_data.button2.grid(row=4, column=2, sticky=W, padx=2, pady=4)

    def connect_via_ssh(self):
        if main.global_data.session.assert_connection():
            main.global_data.progress.step(30)
            main.global_data.connection_exist = True
            main.global_data.status_label.config(text="Connected", foreground="green")
            main.global_data.session.start_threads()
            self.cpu_number = main.global_data.session.get_cpu_num()
            main.global_data.button2.config(state="normal")
            self.de_pickle_session()
            self.top.destroy()
            self.master.deiconify()

        else:
            self.disconnect()
            messagebox.showerror("Error", "Connection refused: check credentials and ip.")
            main.global_data.progress.grid_remove()
            main.global_data.button2.config(state="normal")
            main.global_data.progress.config(value=0)
            return

    def update_credentials(self, host, user, password):
        # First update the credentials of the config file.
        main.global_data.button2.config(state="disabled")
        if password == "" or user == "" or host == "":
            messagebox.showerror("Error", "Fill all the entry fields.")
            return
        if host.count('.') == 3:
            main.global_data.status_label.config(text="Connecting...", foreground="orange")
            if not password == base64.b64decode(config.password).decode():
                encoded_password = base64.b64encode(password.encode())
            else:
                encoded_password = config.password
            with open("config.py", "w") as sf:
                sf.write(f"host = \"{host}\" \nuser = \"{user}\" \npassword = {encoded_password}")
            reload(config)
            if main.global_data.connection_exist:
                if main.global_data.session.is_connected:
                    self.disconnect()
            main.global_data.progress.grid()
            main.global_data.session = session.Session(config.host, config.user, base64.b64decode(config.password).decode())
            main.global_data.host = config.host
            main.global_data.progress.step(30)
            t = threading.Thread(target=self.connect_via_ssh)
            t.start()
            main.global_data.iplabel.config(text=host)
        else:
            messagebox.showerror("Error", "Invalid IP")
            main.global_data.progress.grid_remove()
            main.global_data.button2.config(state="normal")

    def disconnect(self):
        # STOP QUEUE
        self.pickle_session()
        main.global_data.queue_running = False
        main.global_data.status_button.config(text="Start Queue")
        main.global_data.status_queue_label.config(text="Stopped", foreground="red")
        # SESSION OFF
        main.global_data.session.flag_stop = True
        main.global_data.status_label.config(text="Disconnected", foreground="red")
        main.global_data.connection_exist = False
        main.global_data.session.ssh.close()
        self.disconnected_ui()
        self.set_null()

    @staticmethod
    def set_null():
        for label in main.global_data.disk_storage:
            label.config(text="--")
        for label in main.global_data.ram_stats:
            label.config(text="--")
        for label in main.global_data.cpu_list:
            label.config(text="--")

    @staticmethod
    def disconnected_ui():
        main.global_data.heap_queue = []
        main.global_data.projects_queue = []
        main.global_data.data_table = []
        main.global_data.my_list.update(False)

    @staticmethod
    def de_pickle_session():
        try:
            with open("object.pickle", "rb") as f:
                stored_data = pickle.load(f)
                for saved_session in stored_data:
                    if main.global_data.host == saved_session[0]:
                        main.global_data.heap_queue = saved_session[1]
                        main.global_data.projects_queue = saved_session[2]
                        main.global_data.data_table = saved_session[3]
        except EOFError:
            pass
        main.global_data.progress.step(9.99)
        main.global_data.my_list.update()

    @staticmethod
    def pickle_session():
        if not main.global_data.queue_running and not main.global_data.my_list.project_running():
            try:
                with open("object.pickle", "rb") as r:
                    stored_data = pickle.load(r)
            except EOFError:
                stored_data = []
            saved = False
            for session_saved in stored_data:
                if session_saved[0] == main.global_data.host:
                    session_saved[1] = main.global_data.heap_queue
                    session_saved[2] = main.global_data.projects_queue
                    session_saved[3] = main.global_data.data_table
                    saved = True
            if not saved:
                stored_data.append(
                    [main.global_data.host, main.global_data.heap_queue, main.global_data.projects_queue, main.global_data.data_table])
            with open("object.pickle", "wb") as w:
                pickle.dump(stored_data, w)
        elif main.global_data.queue_running:
            messagebox.showwarning("Warning", "Stop the queue before disconnecting.")
        else:
            messagebox.showwarning("Warning", "Wait for project to stop running disconnecting.")

    @staticmethod
    def ask_exit():
        result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
        if result == 'yes':
            main.root.quit()
        else:
            return

    @staticmethod
    def count_queued_project():
        return len(main.global_data.heap_queue) + 1

    @staticmethod
    def bashify(file_path):
        file_path = file_path.split("/")
        new_file_path = ""
        for i in range(len(file_path) - 1, -1, -1):
            if i == len(file_path) - 1:
                new_file_path = f"/{file_path[i]}"
            elif file_path[i].count(".") == 3:
                return new_file_path
            else:
                new_file_path = f"/{file_path[i]}" + new_file_path

    @staticmethod
    def is_repeated(data):
        for obj in main.global_data.projects_queue:
            if obj.name == data:
                return True
        return False
