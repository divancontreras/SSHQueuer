# External Imports
import base64
import heapq
import threading
from datetime import datetime
from importlib import reload
from tkinter import *
from tkinter import ttk, filedialog, Frame, Label, messagebox
import pickle
# Local Imports
import auxiliary_classes
import listbox
import session
import config
from auxiliary_classes import Project


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self ,master)
        self.master = master
        self.master.iconbitmap(r'resources/app_pictogram_orC_icon.ico')
        auxiliary_classes.global_data.connection_exist = False
        auxiliary_classes.global_data.session = None
        self.master.withdraw()
        self.enter_credentials_widget()
        self.init_window()
        self.cpu_number = 0
        self.queue_thread = threading.Thread()

    def StartMove(self, event):
        self.top.x = event.x
        self.top.y = event.y

    def StopMove(self, event):
        self.top.x = None
        self.top.y = None

    def OnMotion(self, event):
        deltax = event.x - self.top.x
        deltay = event.y - self.top.y
        x = self.top.winfo_x() + deltax
        y = self.top.winfo_y() + deltay
        self.top.geometry("+%s+%s" % (x, y))

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
        auxiliary_classes.global_data.menu_connection = Menu(self.master)

        # create a pulldown menu, and add it to the menu bar
        Menu(auxiliary_classes.global_data.menu_connection, tearoff=0)
        setting_menu = Menu(auxiliary_classes.global_data.menu_connection, tearoff=0)
        setting_menu.add_command(label='Auto queueing', command=self.save_action)
        # connect_menu.add_separator()
        auxiliary_classes.global_data.menu_connection.add_cascade(label="Disconnect", command=self.ask_disconnection)
        auxiliary_classes.global_data.menu_connection.add_cascade(label="Settings", menu=setting_menu)
        auxiliary_classes.global_data.menu_connection.add_cascade(label="Exit", command=self.ask_exit)

        self.master.config(menu=auxiliary_classes.global_data.menu_connection)
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
        auxiliary_classes.global_data.iplabel = Label(connection_frame, text=config.host)
        auxiliary_classes.global_data.iplabel.grid(row=0, column=1, sticky=E)
        Label(connection_frame, text="Connection Status:").grid(row=1, column=0, sticky=W)
        Label(connection_frame, text="Queue Status:").grid(row=2, column=0, sticky=W)
        auxiliary_classes.global_data.status_label = Label(connection_frame, text="Disconnected", foreground="red")
        auxiliary_classes.global_data.status_queue_label = Label(connection_frame, text="Stopped", foreground="red")
        auxiliary_classes.global_data.status_label.grid(row=1, column=1, sticky=E)
        auxiliary_classes.global_data.status_queue_label.grid(row=2, column=1, sticky=E)
        Label(cpu_frame, text="CPU", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(cpu_frame, text="CPU 0:").grid(row=1, column=0, sticky=E)
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        auxiliary_classes.global_data.cpu_list[0].grid(row=1, column=1, sticky=W)
        Label(cpu_frame, text="CPU 1:").grid(row=2, column=0, sticky=E)
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        auxiliary_classes.global_data.cpu_list[1].grid(row=2, column=1, sticky=W)
        Label(cpu_frame, text="CPU 2:").grid(row=1, column=2, sticky=E)
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        auxiliary_classes.global_data.cpu_list[2].grid(row=1, column=3, sticky=W)
        Label(cpu_frame, text="CPU 3:").grid(row=2, column=2, sticky=E)
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_frame, text="--"))
        auxiliary_classes.global_data.cpu_list[3].grid(row=2, column=3, sticky=W)
        Label(ram_frame, text="RAM", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(ram_frame, text="total:").grid(row=1, column=0, sticky=E, padx=(10, 0))
        auxiliary_classes.global_data.ram_stats.append(Label(ram_frame, text="--"))
        auxiliary_classes.global_data.ram_stats[0].grid(row=1, column=1, sticky=W)
        Label(ram_frame, text="used:").grid(row=2, column=0, sticky=E, padx=(10, 0))
        auxiliary_classes.global_data.ram_stats.append(Label(ram_frame, text="--"))
        auxiliary_classes.global_data.ram_stats[1].grid(row=2, column=1, sticky=W)
        Label(ram_frame, text="free:").grid(row=1, column=2, sticky=E)
        auxiliary_classes.global_data.ram_stats.append(Label(ram_frame, text="--"))
        auxiliary_classes.global_data.ram_stats[2].grid(row=1, column=3, sticky=W)
        Label(ram_frame, text="usage:").grid(row=2, column=2, sticky=E)
        auxiliary_classes.global_data.ram_stats.append(Label(ram_frame, text="--"))
        auxiliary_classes.global_data.ram_stats[3].grid(row=2, column=3, sticky=W)
        Label(disk_frame, text="Disk", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W)
        Label(disk_frame, text="total:").grid(row=1, column=0, sticky=E, padx=(10, 0))
        auxiliary_classes.global_data.disk_storage.append(Label(disk_frame, text="--"))
        auxiliary_classes.global_data.disk_storage[0].grid(row=1, column=1, sticky=W)
        Label(disk_frame, text="used:").grid(row=2, column=0, sticky=E, padx=(10, 0))
        auxiliary_classes.global_data.disk_storage.append(Label(disk_frame, text="--"))
        auxiliary_classes.global_data.disk_storage[1].grid(row=2, column=1, sticky=W)
        Label(disk_frame, text="free:").grid(row=1, column=2, sticky=E)
        auxiliary_classes.global_data.disk_storage.append(Label(disk_frame, text="--"))
        auxiliary_classes.global_data.disk_storage[2].grid(row=1, column=3, sticky=W)
        Label(disk_frame, text="usage:").grid(row=2, column=2, sticky=E)
        auxiliary_classes.global_data.disk_storage.append(Label(disk_frame, text="--"))
        auxiliary_classes.global_data.disk_storage[3].grid(row=2, column=3, sticky=W)
        auxiliary_classes.global_data.my_list = listbox.DDList(center_frame, height=6)
        # Defining buttons
        auxiliary_classes.global_data.delete_button = ttk.Button(bottom_frame, text='Delete', state="disabled",
                                               command=auxiliary_classes.global_data.my_list.delete)
        auxiliary_classes.global_data.delete_button.pack(side=RIGHT, fill=BOTH, padx=(5, 10))
        Button(bottom_frame, text='Add', command=self.add_project).pack(side=RIGHT, fill=Y, padx=(10, 0))
        auxiliary_classes.global_data.status_button = Button(bottom_frame, text='Start Queue', command=self.toggle_queue_status)
        auxiliary_classes.global_data.status_button.pack(side=LEFT, padx=(10, 0))

        # Config of frames
        title_frame.grid_propagate(False)
        cpu_frame.grid_propagate(False)
        ram_frame.grid_propagate(False)
        disk_frame.grid_propagate(False)

    def toggle_queue_status(self):
        if not auxiliary_classes.global_data.queue_running:
            print(auxiliary_classes.global_data.heap_queue)
            auxiliary_classes.global_data.queue_running = True
            auxiliary_classes.global_data.status_button.config(text="Stop Queue")
            auxiliary_classes.global_data.status_queue_label.config(text="Running", foreground="green")
            if not self.queue_thread.isAlive():
                self.queue_thread = threading.Thread(target=self.start_queue)
                self.queue_thread.start()
        else:
            auxiliary_classes.global_data.queue_running = False
            auxiliary_classes.global_data.status_button.config(text="Start Queue")
            auxiliary_classes.global_data.status_queue_label.config(text="Stopped", foreground="red")

    def save_action(self):
        pass

    def add_project(self):
        reload(config)
        targetpath = f"\\\\{config.host}\\Projects"
        filepath = filedialog.askopenfilename(parent=auxiliary_classes.root, filetypes=(("Script Files", "*.SCRIPT"),
                                                                      ("All Files", "*.*")),
                                              initialdir=targetpath,
                                              title='Please select a .SCRIPT project')
        if len(filepath) > 0:
            self.add_to_queue(filepath)

    def start_queue(self):
        while auxiliary_classes.global_data.queue_running:
            print(auxiliary_classes.global_data.heap_queue)
            if len(auxiliary_classes.global_data.heap_queue) > 0:
                task = auxiliary_classes.global_data.heap_queue[0]
            else:
                messagebox.showwarning("Queue finished", "The queue has finished!")
                self.toggle_queue_status()
                return
            for proj in auxiliary_classes.global_data.projects_queue:
                if proj.name == task[1]:
                    if proj.status == "Running":
                        break
                    else:
                        proj.status = "Running"
                        auxiliary_classes.global_data.my_list.update()
                        auxiliary_classes.global_data.task_done = False
                        auxiliary_classes.global_data.task_stopped = False
                        auxiliary_classes.global_data.task_canceled = False
                        auxiliary_classes.global_data.task_denied = False
                        threading.Thread(target=auxiliary_classes.global_data.session.start_project,
                                         args=(proj.bash_path, proj.name)).start()
                        break
            while True:
                if auxiliary_classes.global_data.task_done:
                    if auxiliary_classes.global_data.task_stopped:
                        proj.status = "Stopped Gently"
                    elif auxiliary_classes.global_data.task_canceled:
                        proj.status = "Stop Forced"
                    elif auxiliary_classes.global_data.task_denied:
                        proj.status = "Permission Denied"
                    else:
                        proj.status = "Completed"
                    proj.turn = None
                    del auxiliary_classes.global_data.name_pid[proj.name]
                    heapq.heappop(auxiliary_classes.global_data.heap_queue)
                    auxiliary_classes.global_data.my_list.adjust_queue_turn()
                    try:
                        auxiliary_classes.global_data.my_list.update()
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
        heapq.heappush(auxiliary_classes.global_data.heap_queue, [int(self.count_queued_project()), filename])
        auxiliary_classes.global_data.projects_queue.append(new)
        auxiliary_classes.global_data.my_list.insert(new.get_list())
        auxiliary_classes.global_data.my_list.update()

    def connect_via_ssh(self):
        if auxiliary_classes.global_data.session.assert_connection():
            auxiliary_classes.global_data.progress.step(30)
            auxiliary_classes.global_data.connection_exist = True
            auxiliary_classes.global_data.status_label.config(text="Connected", foreground="green")
            auxiliary_classes.global_data.session.start_threads()
            self.cpu_number = auxiliary_classes.global_data.session.get_cpu_num()
            auxiliary_classes.global_data.button2.config(state="normal")
            self.de_pickle_session()
            self.top.destroy()
            self.master.deiconify()

        else:
            self.disconnect()
            messagebox.showerror("Error", "Connection refused: check credentials and ip.")
            auxiliary_classes.global_data.progress.place_forget()
            auxiliary_classes.global_data.button2.config(state="normal")
            auxiliary_classes.global_data.progress.config(value=0)
            return

    def enter_credentials_widget(self):
        self.top = Toplevel(self.master)
        self.center(self.top)
        # Removing bordes and adding motion
        self.top.overrideredirect(1)
        self.top.bind("<ButtonPress-1>", self.StartMove)
        self.top.bind('<ButtonRelease-1>', self.StopMove)
        self.top.bind("<B1-Motion>", self.OnMotion)
        self.top.bind("<Return>", lambda event: self.update_credentials(host.get(),
                                                            user.get(),
                                                            password.get()))
        # Window size
        self.top.geometry("676x480")

        # Configuring Main window frames
        left_frame = Frame(self.top, width=376, height=480)
        right_frame = Frame(self.top, width=300, height=480)
        left_frame.pack(side=LEFT)
        right_frame.pack(side=RIGHT, fill=BOTH)

        # Auxiliary right frames
        r_top_frame = Frame(right_frame, width=300, height=40)
        r_entry_frame = Frame(right_frame, width=300, height=180)
        r_buttons_frame = Frame(right_frame, width=300, height=170)
        r_loading_frame = Frame(right_frame, width=300, height=40)
        r_footer_frame = Frame(right_frame, width=300, height=50)
        r_top_frame.pack(fill=BOTH, pady=(0, 8))
        r_entry_frame.pack(fill=BOTH, pady=(40, 8))
        r_buttons_frame.pack(fill=BOTH, pady=8)
        r_loading_frame.pack(expand=True,fill=BOTH, pady=8)
        r_footer_frame.pack(fill=BOTH, pady=8)
        exit_button = Button(r_top_frame, text="X", font=('Arial',11,'bold'), fg = "grey")
        exit_button.config(relief=FLAT)
        exit_button.bind('<Button-1>', quit)
        exit_button.pack(side=RIGHT)
        img = PhotoImage(file=r'resources\Cover_Lines.png')
        self.master.one = Label(left_frame, image=img)
        self.master.one.photo = img
        self.master.one.pack(side=RIGHT)
        img = PhotoImage(file=r'resources\LOGO_SE.png')
        self.master.two = Label(r_footer_frame, image=img)
        self.master.two.photo = img
        self.master.two.pack(side=RIGHT)
        auxiliary_classes.global_data.progress = ttk.Progressbar(r_loading_frame, length=100, value=0)
        host = StringVar(value="Host")
        user = StringVar(value="User")
        password = StringVar(value="Password")
        var = StringVar()
        self.top.title("Connect to machine")
        self.top.resizable(width=False, height=False)
        # host.set(config.host)
        # user.set(config.user)
        # password.set(base64.b64decode(config.password).decode())

        e1 = ttk.Entry(r_entry_frame, textvariable=host, font=('Arial', 15, 'italic'))
        e2 = ttk.Entry(r_entry_frame, textvariable=user, font=('Arial', 15, 'italic'))
        e3 = ttk.Entry(r_entry_frame, textvariable=password, font=('Arial', 15, 'italic'))
        e1.config({"foreground":"grey"})
        e2.config({"foreground":"grey"})
        e3.config({"foreground":"grey"})
        e3.config(show="*")
        e1.pack(pady=(30,8))
        e2.pack(pady=8)
        e3.pack(pady=8)
        auxiliary_classes.global_data.progress.place(relx=0.5, rely=0.5, anchor=CENTER)
        auxiliary_classes.global_data.progress.place_forget()
        check_button = ttk.Checkbutton(
            r_buttons_frame, text="Remember me", variable=var,
            onvalue="RGB", offvalue="L")
        check_button.pack(side=TOP, pady=8)
        imag_last = PhotoImage(file=r'resources\Button_last-session.png')
        button1 = Button(r_buttons_frame, command=quit)
        button1.config(image=imag_last, bd=0, width="240", height="32")
        button1.photo = imag_last
        login_img = PhotoImage(file=r'resources\button_login.png')
        auxiliary_classes.global_data.button2 = Button(r_buttons_frame, text="Connect",
                                                            command=lambda: self.update_credentials(host.get(),
                                                            user.get(),
                                                            password.get()))
        auxiliary_classes.global_data.button2.config(image=login_img, bd=0, width="240", height="32")
        auxiliary_classes.global_data.button2.photo = login_img
        auxiliary_classes.global_data.button2.pack(pady=5)
        button1.pack(pady=8)

    def update_credentials(self, host, user, password):
        # First update the credentials of the config file.
        auxiliary_classes.global_data.button2.config(state="disabled")
        if password == "" or user == "" or host == "":
            messagebox.showerror("Error", "Fill all the entry fields.")
            return
        if host.count('.') == 3:
            auxiliary_classes.global_data.status_label.config(text="Connecting...", foreground="orange")
            if not password == base64.b64decode(config.password).decode():
                encoded_password = base64.b64encode(password.encode())
            else:
                encoded_password = config.password
            with open("config.py", "w") as sf:
                sf.write(f"host = \"{host}\" \nuser = \"{user}\" \npassword = {encoded_password}")
            reload(config)
            if auxiliary_classes.global_data.connection_exist:
                if auxiliary_classes.global_data.session.is_connected:
                    self.disconnect()
            auxiliary_classes.global_data.progress.place(relx=0.5, rely=0.5, anchor=CENTER)
            auxiliary_classes.global_data.session = session.Session(config.host, config.user, base64.b64decode(config.password).decode())
            auxiliary_classes.global_data.host = config.host
            auxiliary_classes.global_data.progress.step(30)
            t = threading.Thread(target=self.connect_via_ssh)
            t.start()
            auxiliary_classes.global_data.iplabel.config(text=host)
        else:
            messagebox.showerror("Error", "Invalid IP")
            auxiliary_classes.global_data.progress.place_forget()
            auxiliary_classes.global_data.button2.config(state="normal")

    def disconnect(self):
        # STOP QUEUE
        self.pickle_session()
        auxiliary_classes.global_data.queue_running = False
        auxiliary_classes.global_data.status_button.config(text="Start Queue")
        auxiliary_classes.global_data.status_queue_label.config(text="Stopped", foreground="red")
        # SESSION OFF
        auxiliary_classes.global_data.session.flag_stop = True
        auxiliary_classes.global_data.status_label.config(text="Disconnected", foreground="red")
        auxiliary_classes.global_data.connection_exist = False
        auxiliary_classes.global_data.session.ssh.close()
        self.disconnected_ui()
        self.set_null()

    @staticmethod
    def set_null():
        for label in auxiliary_classes.global_data.disk_storage:
            label.config(text="--")
        for label in auxiliary_classes.global_data.ram_stats:
            label.config(text="--")
        for label in auxiliary_classes.global_data.cpu_list:
            label.config(text="--")

    @staticmethod
    def disconnected_ui():
        auxiliary_classes.global_data.heap_queue = []
        auxiliary_classes.global_data.projects_queue = []
        auxiliary_classes.global_data.data_table = []
        auxiliary_classes.global_data.my_list.update(False)

    @staticmethod
    def de_pickle_session():
        try:
            with open("object.pickle", "rb") as f:
                stored_data = pickle.load(f)
                for saved_session in stored_data:
                    if auxiliary_classes.global_data.host == saved_session[0]:
                        auxiliary_classes.global_data.heap_queue = saved_session[1]
                        auxiliary_classes.global_data.projects_queue = saved_session[2]
                        auxiliary_classes.global_data.data_table = saved_session[3]
        except EOFError:
            pass
        auxiliary_classes.global_data.progress.step(9.99)
        auxiliary_classes.global_data.my_list.update()

    @staticmethod
    def pickle_session():
        if not auxiliary_classes.global_data.queue_running and not auxiliary_classes.global_data.my_list.project_running():
            try:
                with open("object.pickle", "rb") as r:
                    stored_data = pickle.load(r)
            except EOFError:
                stored_data = []
            saved = False
            for session_saved in stored_data:
                if session_saved[0] == auxiliary_classes.global_data.host:
                    session_saved[1] = auxiliary_classes.global_data.heap_queue
                    session_saved[2] = auxiliary_classes.global_data.projects_queue
                    session_saved[3] = auxiliary_classes.global_data.data_table
                    saved = True
            if not saved:
                stored_data.append(
                    [auxiliary_classes.global_data.host, auxiliary_classes.global_data.heap_queue, auxiliary_classes.global_data.projects_queue, auxiliary_classes.global_data.data_table])
            with open("object.pickle", "wb") as w:
                pickle.dump(stored_data, w)
        elif auxiliary_classes.global_data.queue_running:
            messagebox.showwarning("Warning", "Stop the queue before disconnecting.")
        else:
            messagebox.showwarning("Warning", "Wait for project to stop running disconnecting.")

    @staticmethod
    def ask_exit():
        result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
        if result == 'yes':
            auxiliary_classes.root.quit()
        else:
            return

    @staticmethod
    def count_queued_project():
        return len(auxiliary_classes.global_data.heap_queue) + 1

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
                new_file_path = f'/{file_path[i]}' + new_file_path

    @staticmethod
    def center(win):
        w = win.winfo_screenwidth()
        h = win.winfo_screenheight()
        win.geometry("400x300+%d+%d" % ((w - 400) / 2, (h - 300) / 2))

    @staticmethod
    def is_repeated(data):
        for obj in auxiliary_classes.global_data.projects_queue:
            if obj.name == data:
                return True
        return False
