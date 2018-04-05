# External Imports
import base64
import heapq
import threading
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, Frame, Label, messagebox, font
import pickle
# Local Imports
import os
import listbox
import session
from auxiliary_classes import Project, SessionSaver, SessionData, SessionConfig


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.heap_queue = []
        self.name_pid = {}
        self.name_mpid = {}
        self.projects_list = []
        self.unpickle_creds()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master = master
        self.master.withdraw()
        self.master.iconbitmap(r'resources/app_pictogram_orC_icon.ico')
        self.session = None
        self.enter_credentials_widget()
        self.init_window()
        self.last_session_exist = False
        self.cpu_number = 0
        self.queue_thread = threading.Thread()
        self.task_done = False
        self.task_stopped = False
        self.task_canceled = False
        self.task_denied = False
        self.queue_running = False

    def start_move(self, event):
        self.top.x = event.x
        self.top.y = event.y

    def stop_move(self, event):
        self.top.x = None
        self.top.y = None

    def on_motion(self, event):
        delta_x = event.x - self.top.x
        delta_y = event.y - self.top.y
        x = self.top.winfo_x() + delta_x
        y = self.top.winfo_y() + delta_y
        self.top.geometry("+%s+%s" % (x, y))

    def new_connection(self, e):
        self.toggle_underline(e)
        self.disconnect()
        self.master.withdraw()
        self.enter_credentials_widget()
        
    def ask_disconnection(self):
        result = messagebox.askquestion("Disconnect", "Are  you sure you want to disconnect?", icon='warning')
        if result == 'yes':
            self.new_connection()
        else:
            return

    def toggle_underline(self, event):
        f = font.Font(event.widget, event.widget.cget("font"))
        if f.cget("underline") != 1:
            f.configure(underline=True)
        else:
            f.configure(underline=False)
        event.widget.configure(font=f)

    def init_window(self):
        # Init window, set title and geomtry of window.
        self.master.title("SimQ")
        self.master.geometry("1024x664")
        self.master.pack_propagate(0)

        """Declaration of outer frames"""
        # Declaration frames of the UI and configuring.
        header_frame = Frame(self.master, width=1024, height=62)
        settings_frame = Frame(self.master, width=1024, height=40, bg="#3dcd58")
        bottom_queue = Frame(self.master, width=1024, height=570, padx=3, bg="#e0dede")
        queue_frame = Frame(bottom_queue, width=736, height=570, padx=10, borderwidth=1)
        queue_frame.config(relief=RIDGE)
        stats_frame = Frame(bottom_queue, width=288, bg="#e0dede")
        header_frame.pack(fill=BOTH)
        settings_frame.pack(fill=BOTH)
        bottom_queue.pack(fill=BOTH, expand=True)
        stats_frame.pack(side=LEFT, padx=(16,8), pady=16)
        queue_frame.pack(side=RIGHT, padx=(8,16), pady=16, fill=BOTH, expand=True)

        """Declaration of inner frames"""
        # Header_frame needs icon, Name of the Tool, Connection stats, Project completion stats, Disconnect option
        img = PhotoImage(file=r'resources\Header_icon_simq.png')
        icon_frame = Label(header_frame, height=62, width=121, image=img, highlightthickness=0, borderwidth=0)
        icon_frame.photo = img
        icon_frame.pack(side=LEFT, fill=BOTH)
        disconnect_button = Button(header_frame, text="Disconnect", fg="#42b4e6", font=("Arial", 11))
        disconnect_button.config(relief=FLAT, padx=3)
        disconnect_button.bind("<Button-1>", self.new_connection)
        disconnect_button.bind("<Enter>", self.toggle_underline)
        disconnect_button.bind("<Leave>", self.toggle_underline)
        disconnect_button.pack(side=RIGHT)
        connection_frame = Frame(header_frame, width=260, height=90)
        connection_frame.pack(side=RIGHT)

        # settings_frame will just have a label frame for text (for now).
        text = Label(settings_frame, text="Settings", font=("Arial", 12), fg="white", bg="#3dcd58")
        text.pack(side=LEFT, anchor="center", padx=5)

        # stats_frame need's three stats frames CPU, RAM and DISK.
        status_frame = Frame(stats_frame, width=256, height=128, borderwidth=1, relief=RIDGE)
        cpu_frame = Frame(stats_frame, width=256, height=128, borderwidth=1, relief=RIDGE)
        ram_frame = Frame(stats_frame, width=256, height=128, borderwidth=1, relief=RIDGE)
        disk_frame = Frame(stats_frame, width=256, height=128, borderwidth=1, relief=RIDGE)
        status_frame.pack(expand=True)
        cpu_frame.pack(pady=16, expand=True)
        ram_frame.pack(pady=(0, 16), expand=True)
        disk_frame.pack(fill=Y, expand=True)

        # queue_frame will have 3 frames, one for header text,
        # one for processing of tasks, one for listbox and one for two buttons
        header_listbox = Frame(queue_frame, width=664, height=100)
        aux_frame = Frame(header_listbox, height=50)
        aux_frame.pack(fill=BOTH)
        img = PhotoImage(file=r'resources\simulation_queue.png')
        icon_frame = Label(aux_frame, height=19, width=186, image=img, highlightthickness=0, borderwidth=0)
        icon_frame.photo = img
        icon_frame.pack(anchor="w", pady=5)
        ttk.Separator(aux_frame, orient=HORIZONTAL).pack(fill=X, expand=True)
        progress_frame = Frame(header_listbox, height=10)
        progress_frame.pack(fill=BOTH, pady=5)
        s = ttk.Style()
        self.cute_tag = Label(progress_frame, text="On hold", font=("Arial", 10, "bold"),
                                           fg="#3dcd58")
        self.cute_tag.pack(side=LEFT, anchor="w")
        s.configure("red.Horizontal.TProgressbar", foreground='green', background='#3dcd58', theme="alt")
        self.progress_project = ttk.Progressbar(progress_frame,
                                                                         style="red.Horizontal.TProgressbar",
                                                                         orient="horizontal",
                                                                         value=1,
                                                                         length=100,
                                                                         mode="determinate", maximum=100)

        listbox_frame = Frame(queue_frame, width=664, height=208)
        bottom_queue = Frame(queue_frame, width=830, height=50, pady=5)
        header_listbox.pack(fill=BOTH)
        listbox_frame.pack(fill=BOTH, expand=True)
        bottom_queue.pack(fill=BOTH)
        self.treeview = listbox.DDList(listbox_frame, self, height=5)

        # Configuring Connection frame
        img = PhotoImage(file=r'resources\User_picto.png')
        icon_frame = Label(connection_frame, image=img, highlightthickness=0, borderwidth=0)
        icon_frame.photo = img
        icon_frame.pack(side=LEFT, anchor="e")
        self.iplabel = Label(connection_frame, text=self.active_session.host, fg="#3dcd58",
                             font=("Arial", 10,"bold"))
        self.username = Label(connection_frame, text=self.active_session.user, fg="#3dcd58",
                              font=("Arial", 12, "bold"))
        self.username.pack(side=TOP, anchor="w")
        self.iplabel.pack(side=BOTTOM, anchor="w")
        # Label(connection_frame, text="Queue Status:").grid(row=2, column=0, sticky=W)
        # self.status_queue_label = Label(connection_frame, text="Stopped", foreground="red")

        # Config Status Frame
        status_header = Frame(status_frame, width=256, height=32)
        status_header.pack(side=TOP, fill=BOTH)
        status_body = Frame(status_frame, width=256, height=100)
        status_body.pack(side=BOTTOM, fill=BOTH)
        status_tag = Frame(status_body, width=32, height=100, bg="#e8e8e8")
        status_tag.pack(side=LEFT)
        status_val = Frame(status_body, width=32, height=100, bg="#e8e8e8")
        status_val.pack(side=LEFT)
        right_val = Frame(status_body, width=32, height=100)
        right_val.pack(side=LEFT, fill=BOTH, expand=True)
        Label(right_val, text="Running Info", font=("Arial", 11, "bold")).pack(side=TOP)
        left_aux = Frame(right_val, width=16)
        left_aux.pack(side=LEFT, fill=BOTH, expand=True)
        right_aux = Frame(right_val, width=16)
        right_aux.pack(side=LEFT, fill=BOTH, expand=True)
        Label(left_aux, text="Name:", font=("Arial", 10)).pack()
        Label(left_aux, text="Percentage:", font=("Arial", 10)).pack()
        Label(left_aux, text="Iteration:", font=("Arial", 10)).pack()
        Label(left_aux, text="ETC:", font=("Arial", 10)).pack()
        self.project_name = Label(right_aux, text="--", font=("Arial", 10))
        self.project_percentage = Label(right_aux, text="--", font=("Arial", 10))
        self.project_iteration = Label(right_aux, text="--", font=("Arial", 10))
        self.project_etc = Label(right_aux, text="--", font=("Arial", 10))

        self.project_name.pack()
        self.project_percentage.pack()
        self.project_iteration.pack()
        self.project_etc.pack()
        img = PhotoImage(file=r'resources\Status_header.png')
        one = Label(status_header, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=TOP, anchor="w")
        ttk.Separator(status_header, orient=HORIZONTAL).pack(side=BOTTOM, fill=X, expand=True)
        img = PhotoImage(file=r'resources\completed_picto.png')
        one = Label(status_tag, image=img, highlightthickness=0, borderwidth=0, bg="#e8e8e8")
        one.photo = img
        one.pack(padx=2)
        self.completed_val = Label(status_val, text="0", font=("Arial", 12), bg="#e8e8e8")
        self.completed_val.pack(side=TOP, anchor="w", pady=3, padx=3)
        img = PhotoImage(file=r'resources\error_picto.png')
        one = Label(status_tag, image=img, highlightthickness=0, borderwidth=0, bg="#e8e8e8")
        one.photo = img
        one.pack(padx=2)
        self.error_val = Label(status_val, text="0", font=("Arial", 12), bg="#e8e8e8")
        self.error_val.pack(side=TOP, anchor="w", pady=3, padx=3)
        img = PhotoImage(file=r'resources\information_picto.png')
        one = Label(status_tag, image=img, highlightthickness=0, borderwidth=0, bg="#e8e8e8")
        one.photo = img
        one.pack(padx=2)
        self.info_val = Label(status_val, text="0", font=("Arial", 12), bg="#e8e8e8")
        self.info_val.pack(side=TOP, anchor="w", pady=3, padx=3)
        img = PhotoImage(file=r'resources\warning_picto.png')
        one = Label(status_tag, image=img, highlightthickness=0, borderwidth=0, bg="#e8e8e8")
        one.photo = img
        one.pack(padx=2)
        self.warning_val = Label(status_val, text="0", font=("Arial", 12), bg="#e8e8e8")
        self.warning_val.pack(side=TOP, anchor="w", pady=3, padx=3)
        self.status_avg = Label(status_body, text="--", font=("Arial", 11, "bold"))

        # Configuring Cpu stats frame

        cpu_header = Frame(cpu_frame, width=256, height=32)
        cpu_header.pack(side=TOP, fill=BOTH)
        cpu_body = Frame(cpu_frame, width=256, height=100)
        cpu_body.pack(side=BOTTOM, fill=BOTH, expand=True)
        cpu_body_left = Frame(cpu_body, width=128, height=100, bg="#e8e8e8")
        cpu_body_left.pack(side=LEFT, fill=BOTH, expand=True)
        cpu_body_right = Frame(cpu_body, width=128, height=100)
        cpu_body_right.pack(side=RIGHT, fill=BOTH, expand=True)
        cpu_tag = Frame(cpu_body_left, width=64, height=100, bg="#e8e8e8")
        cpu_tag.pack(side=LEFT, fill=BOTH, expand=True)
        cpu_val = Frame(cpu_body_left, width=64, height=100, bg="#e8e8e8")
        cpu_val.pack(side=RIGHT, fill=BOTH, expand=True)
        img = PhotoImage(file=r'resources\CPU_header.png')
        one = Label(cpu_header, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=TOP, anchor="w")
        ttk.Separator(cpu_header, orient=HORIZONTAL).pack(side=BOTTOM, fill=X, expand=True)
        Label(cpu_tag, text="CPU 0:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.cpu_stats_0 = Label(cpu_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                            fg="#333333")
        self.cpu_stats_0.pack(fill=BOTH, expand=True, padx=4)
        Label(cpu_tag, text="CPU 1:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.cpu_stats_1 = Label(cpu_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                            fg="#333333")
        self.cpu_stats_1.pack(fill=BOTH, padx=4, expand=True)
        Label(cpu_tag, text="CPU 2:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.cpu_stats_2 = Label(cpu_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                            fg="#333333")
        self.cpu_stats_2.pack(fill=BOTH, padx=4, expand=True)
        Label(cpu_tag, text="CPU 3:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.cpu_stats_3 = Label(cpu_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                            fg="#333333")
        self.cpu_stats_3.pack(fill=BOTH, padx=4, expand=True)
        self.cpu_avg = Label(cpu_body_right, text="--",
                                                      font=("Arial", 16, "bold"))
        self.cpu_avg.pack(side=BOTTOM)
        Label(cpu_body_right, text="USAGE", font=("Arial", 8, "bold"), foreground="gray").pack(side=BOTTOM , anchor="w",
                                                                                               pady=(5, 0))

        # Configuring RAM stats frame
        ram_header = Frame(ram_frame, width=256, height=32)
        ram_header.pack(side=TOP, fill=BOTH)
        ram_body = Frame(ram_frame, width=256, height=60)
        ram_body.pack(side=BOTTOM, fill=BOTH, expand=True)
        ram_body_left = Frame(ram_body, width=128, height=100, bg="#e8e8e8")
        ram_body_left.pack(side=LEFT, fill=BOTH, expand=True)
        ram_body_right = Frame(ram_body, width=128, height=100)
        ram_body_right.pack(side=RIGHT, fill=BOTH, expand=True)
        ram_tag = Frame(ram_body_left, width=64, height=100, bg="#e8e8e8")
        ram_tag.pack(side=LEFT, fill=BOTH, expand=True)
        ram_val = Frame(ram_body_left, width=64, height=100, bg="#e8e8e8")
        ram_val.pack(side=RIGHT, fill=BOTH, expand=True)
        img = PhotoImage(file=r'resources\RAM_header.png')
        one = Label(ram_header, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=TOP, anchor="w")
        ttk.Separator(ram_header, orient=HORIZONTAL).pack(side=BOTTOM, fill=X, expand=True)
        Label(ram_tag, text="total:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.ram_stats_0 = Label(ram_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                             fg="#333333")
        self.ram_stats_0.pack()
        Label(ram_tag, text="used:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.ram_stats_1 = Label(ram_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                             fg="#333333")
        self.ram_stats_1.pack()
        Label(ram_tag, text="free:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.ram_stats_2 = Label(ram_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                             fg="#333333")
        self.ram_stats_2.pack()
        self.ram_stats_3 = Label(ram_body_right, text="--",
                                                 font=("Arial", 16, "bold"),
                                                 foreground="green")
        self.ram_stats_3.pack(side=BOTTOM)
        Label(ram_body_right, text="USAGE", font=("Arial", 8, "bold"), foreground="gray").pack(side=BOTTOM,
                                                                                               anchor="w")
        # Configuring Disk stats frame

        disk_header = Frame(disk_frame, width=256, height=32)
        disk_header.pack(side=TOP, fill=BOTH)
        disk_body = Frame(disk_frame, width=100, height=60, bg="#e8e8e8")
        disk_body.pack(side=BOTTOM, fill=BOTH, expand=True)
        disk_body_left = Frame(disk_body, width=85, height=60)
        disk_body_left.pack(side=LEFT, fill=BOTH, expand=True)
        disk_body_right = Frame(disk_body, width=85, height=60)
        disk_body_right.pack(side=RIGHT, fill=BOTH, expand=True)
        disk_tag = Frame(disk_body_left, width=40, height=60, bg="#e8e8e8")
        disk_tag.pack(side=LEFT, fill=BOTH, expand=True)
        disk_val = Frame(disk_body_left, width=40, height=60, bg="#e8e8e8")
        disk_val.pack(side=RIGHT, fill=BOTH, expand=True)

        img = PhotoImage(file=r'resources\Disk_header.png')
        one = Label(disk_header, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=TOP, anchor="w")
        ttk.Separator(disk_header, orient=HORIZONTAL,).pack(side=BOTTOM, fill=X, expand=True)
        Label(disk_tag, text="total:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.disk_storage_0 = Label(disk_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                                fg="#333333")
        self.disk_storage_0.pack()
        Label(disk_tag, text="used:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.disk_storage_1 = Label(disk_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                                fg="#333333")
        self.disk_storage_1.pack()
        Label(disk_tag, text="free:", font=("Arial", 11), bg="#e8e8e8", fg="#333333").pack()
        self.disk_storage_2 = Label(disk_val, text="--", font=("Arial", 10), bg="#e8e8e8",
                                                                fg="#333333")
        self.disk_storage_2.pack()
        self.disk_storage_3 = Label(disk_body_right, text="--", font=("Arial", 16, "bold"),
                                                                foreground="green")
        self.disk_storage_3.pack(side=BOTTOM)
        Label(disk_body_right, text="USAGE", font=("Arial", 8, "bold"), foreground="gray").pack(side=BOTTOM,
                                                                                                anchor="w")

        # Defining buttons for queue_frame
        
        self.delete_button = ttk.Button(bottom_queue,
                                                                 text='Delete', 
                                                                 state="disabled", 
                                                                 command=self.treeview.delete)
        self.delete_button.pack(side=RIGHT, padx=(5, 10))
        ttk.Button(bottom_queue, text='Add', command=self.add_project).pack(side=RIGHT, fill=X, padx=(10, 0))
        self.status_button = ttk.Button(bottom_queue,
                                                                 text='Start',
                                                                 command=self.toggle_queue_status)
        self.status_button.pack(side=LEFT, padx=(10, 0))

        # Config of frames
        stats_frame.grid_propagate(False)
        cpu_frame.grid_propagate(False)
        ram_frame.grid_propagate(False)
        disk_frame.grid_propagate(False)

    def toggle_queue_status(self):
        if not self.queue_running:
            print(self.heap_queue)
            self.queue_running = True
            self.status_button.config(text="Stop")
            if not self.queue_thread.isAlive():
                self.queue_thread = threading.Thread(target=self.start_queue)
                self.queue_thread.start()
        else:
            self.project_iteration.config(
                text="--")
            self.project_percentage.config(
                text="--")
            self.project_etc.config(text="--")
            self.queue_running = False
            self.status_button.config(text="Start")

    def add_project(self):
        target_path = f"\\\\{self.active_session.host}\\Projects"
        file_path = filedialog.askopenfilename(parent=self.master,
                                               filetypes=(("Script Files", "*.SCRIPT"), ("All Files", "*.*")), 
                                               initialdir=target_path, 
                                               title='Please select a .SCRIPT project')
        if len(file_path) > 0:
            self.add_to_queue(file_path)

    def start_queue(self):
        while self.queue_running:
            print(self.heap_queue)
            if len(self.heap_queue) > 0:
                task = self.heap_queue[0]
            else:
                messagebox.showwarning("Queue finished", "The queue has finished!")
                self.toggle_queue_status()
                return
            for proj in self.projects_list:
                if proj.name == task[1]:
                    if proj.is_running():
                        break
                    else:
                        proj.set_running()
                        self.treeview.update()
                        self.reset_flags()
                        threading.Thread(target=self.session.start_project,
                                         args=(proj.bash_path, proj.name)).start()
                        break
            while True:
                if self.task_done:
                    self.progress_project.pack_forget()
                    self.cute_tag.configure(text="On hold")
                    self.project_name.config(text="--")
                    if self.task_stopped:
                        proj.set_saved()
                        self.session.remove_fdstop(proj.bash_path)
                    elif self.task_canceled:
                        proj.set_canceled()
                    elif self.task_denied:
                        proj.set_denied()
                    else:
                        proj.set_completed()
                    proj.turn = 2000
                    del self.name_pid[proj.name]
                    heapq.heappop(self.heap_queue)
                    self.treeview.adjust_queue_turn()
                    try:
                        self.treeview.update()
                    except ReferenceError:
                        return
                    break

    def add_to_queue(self, filepath, icont=0):
        """
        Pops an filedialog window that will ask for the file wanted to be queued
        Then adds an element to the queue both graphical and the heapq"""

        with open(filepath, 'r') as doc:
            data = doc.read()
            try:
                cores = int(data[data.find("-t") + 2])
            except ValueError:
                cores = "N/A"
            tofilename = filepath.split("/")[-1]
            filename = tofilename[:tofilename.find(".")]
            auxfilename = filename
        while self.is_repeated(filename):
            icont += 1
            filename = f"{auxfilename} ({icont})"

        new = Project(filename,"resources\information_picto.png", filepath, cores, "Queued",
                           self.count_queued_project(), datetime.now().strftime("%Y-%m-%d / %H:%M:%S"))
        new.bash_path = self.bashify(filepath)
        print(new.bash_path)
        heapq.heappush(self.heap_queue, [int(self.count_queued_project()), filename])
        self.projects_list.append(new)
        self.treeview.insert(new)
        if not len(self.heap_queue) > 0:
            self.status_button.config(state="disabled")
        else:
            self.status_button.config(state="normal")
        self.count_projects()

    def connect_via_ssh(self):
        if self.session.assert_connection():
            self.progress.step(30)
            self.session.start_threads()
            self.cpu_number = self.session.get_cpu_num()
            self.button2.config(state="normal")
            if self.last_session_exist:
                self.button1.config(state="normal")
            else:
                self.button1.config(state="disabled")
            self.de_pickle_session()
            self.top.destroy()
            self.master.deiconify()

        else:
            self.disconnect()
            self.progress.place_forget()
            self.msg_refused.place(relx=0.5, rely=0.5, anchor=CENTER)
            self.button2.config(state="normal")
            if self.last_session_exist:
                self.button1.config(state="normal")
            else:
                self.button1.config(state="disabled")
            self.progress.config(value=0)
            return

    def enter_credentials_widget(self):
        self.top = Toplevel(self.master)
        self.center(self.top)
        # Removing bordes and adding motion
        self.top.overrideredirect(1)
        self.top.bind("<ButtonPress-1>", self.start_move)
        self.top.bind('<ButtonRelease-1>', self.stop_move)
        self.top.bind("<B1-Motion>", self.on_motion)
        self.top.bind("<Return>", lambda event: self.set_credentials(False, host.get(),
                                                                     user.get(),
                                                                     password.get()))
        # Window size
        self.top.geometry("676x480")

        # Configuring Main window frames
        left_frame = Frame(self.top, width=376, height=480)
        right_frame = Frame(self.top, width=300, height=480)
        left_frame.pack(side=LEFT, fill=BOTH)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # Auxiliary right frames
        r_top_frame = Frame(right_frame, width=300, height=40)
        r_entry_frame = Frame(right_frame, width=300, height=170)
        r_buttons_frame = Frame(right_frame, width=300, height=170)
        r_loading_frame = Frame(right_frame, width=300, height=35)
        r_footer_frame = Frame(right_frame, width=300, height=42)
        r_top_frame.pack(fill=BOTH, pady=(0, 8))
        r_entry_frame.pack(fill=BOTH, pady=(30, 4))
        r_buttons_frame.pack(fill=BOTH, pady=(8, 2))
        r_loading_frame.pack(fill=BOTH, pady=(2, 8))
        r_footer_frame.pack(fill=BOTH)
        exit_button = Button(r_top_frame, text="X", font=('Arial', 11), fg="grey")
        exit_button.config(relief=FLAT)
        exit_button.bind('<Button-1>', self.exit_window)
        exit_button.pack(side=RIGHT)
        img = PhotoImage(file=r'resources\Cover_Lines.png')
        one = Label(left_frame, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=RIGHT)
        img = PhotoImage(file=r'resources\LIO_SE_195x40.png')
        two = Label(r_footer_frame, image=img)
        two.pack(side=RIGHT, padx=(0, 25))
        two.photo = img
        self.progress = ttk.Progressbar(r_loading_frame, length=100, value=0)
        self.msg_refused = Label(r_loading_frame,
                                  text="Connection failed, check credentials and try again.",
                                  fg="red",
                                  font=('Arial', 9, 'italic'))
        self.msg_entry = Label(r_loading_frame,
                                text="Please, fill all entry fields.",
                                fg="red",
                                font=('Arial', 9, 'italic'))
        host = StringVar(value="Host")
        user = StringVar(value="User")
        password = StringVar(value="Password")
        self.checkbox = StringVar()
        self.top.title("Connect to machine")
        self.top.resizable(width=False, height=False)

        e1 = ttk.Entry(r_entry_frame, textvariable=host, font=('Arial', 14, 'italic'), foreground="grey")
        e2 = ttk.Entry(r_entry_frame, textvariable=user, font=('Arial', 14, 'italic'), foreground="grey")
        e3 = ttk.Entry(r_entry_frame, textvariable=password, font=('Arial', 14, 'italic'), foreground="grey")
        e3.config(show="*")
        e1.pack(pady=(25, 8))
        e2.pack(pady=8)
        e3.pack(pady=(8, 0))
        check_button = ttk.Checkbutton(
            r_buttons_frame, text="Remember me", variable=self.checkbox, onvalue=True)
        check_button.pack(side=TOP, anchor=W, padx=(35, 0), pady=(0, 4))
        imag_last = PhotoImage(file=r'resources\LastSession_button.png')
        self.button1 = Button(r_buttons_frame)
        self.button1.config(image=imag_last,
                            bd=0, width="240",
                            height="32",
                            command=lambda: self.get_last_session())
        if self.last_session_exist:
            self.button1.config(state="normal")
        else:
            self.button1.config(state="disabled")
        self.button1.photo = imag_last
        login_img = PhotoImage(file=r'resources\Login_button.png')
        self.button2 = Button(r_buttons_frame,
                              text="Connect",
                              command=lambda: self.set_credentials(False, host.get(),
                                                                   user.get(),
                                                                   password.get()))
        self.button2.config(image=login_img, bd=0, width="240", height="32")
        self.button2.photo = login_img
        self.button2.pack(pady=5)
        self.button1.pack(pady=8)
        self.top.lift()
        self.top.attributes('-topmost', True)

    def exit_window(self,e):
        sys.exit()

    def get_last_session(self):
        self.unpickle_creds()
        self.set_credentials(True, self.active_session.host,
                             self.active_session.user,
                             base64.b64decode(self.active_session.password).decode())

    def set_credentials(self, last_session, host, user, password):
        # First update the credentials of the config file.
        self.msg_refused.place_forget()
        self.msg_entry.place_forget()
        self.button2.config(state="disabled")
        self.button1.config(state="disabled")
        if host == "Host" or host == "":
            self.msg_entry.place(relx=0.5, rely=0.5, anchor=CENTER)
            self.button2.config(state="normal")
            if self.last_session_exist:
                self.button1.config(state="normal")
            else:
                self.button1.config(state="disabled")
            return
        if not last_session:
            if not password == base64.b64decode(self.active_session.password).decode():
                encoded_password = base64.b64encode(password.encode())
            else:
                encoded_password = self.active_session.password
            try:
                with open("object.pickle", "rb") as r:
                    stored_data = pickle.load(r)
                    r.close()
            except EOFError:
                    stored_data = None
            if self.checkbox.get() == '1':
                self.last_session_exist = True
                if stored_data is None:
                    stored_data = SessionSaver([host, user, encoded_password], [], True)
                else:
                    stored_data.last_session = [host, user, encoded_password]
                    stored_data.last_session_exist = True
            else:
                if stored_data is None:
                    stored_data = SessionSaver([], [], False)
            with open("object.pickle", "wb") as w:
                pickle.dump(stored_data, w)
                w.close()
            self.active_session.host = host
            self.active_session.password = encoded_password
            self.active_session.user = user
        else:
            self.active_session = self.last_session
        self.progress.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.session = session.Session(self, self.active_session.host,
                                       self.active_session.user,
                                       base64.b64decode(self.active_session.password).decode())
        self.progress.step(30)
        t = threading.Thread(target=self.connect_via_ssh)
        t.start()
        self.iplabel.config(text=self.active_session.host)


    def disconnect(self):
        # STOP QUEUE
        self.pickle_session()
        self.queue_running = False
        self.status_button.config(text="Start")
        # SESSION OFF
        self.session.flag_stop = True
        self.session.ssh.close()
        self.disconnected_ui()

    def on_closing(self):
        result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
        if result == 'no':
            return
        self.disconnect()
        if not self.queue_running and not self.treeview.project_running():
            with open("object.pickle", "rb") as r:
                stored_data = pickle.load(r)
            saved = False
            for session_saved in stored_data.stored_sessions:
                if session_saved.host == self.active_session.host:
                    session_saved.heap_queue = self.heap_queue
                    session_saved.projects_list = self.projects_list
                    saved = True
            if not saved:
                stored_data.stored_sessions.append(SessionData(self.active_session.host, self.heap_queue,
                                                               self.projects_list))
            with open("object.pickle", "wb") as w:
                pickle.dump(stored_data, w)
            exit()
        elif self.queue_running:
            messagebox.showwarning("Warning", "Stop the queue before exiting the program.")
        else:
            messagebox.showwarning("Warning", "Wait for project to stop running before exiting.")

    def reset_flags(self):
        self.task_done = False
        self.task_stopped = False
        self.task_canceled = False
        self.task_denied = False


    def disconnected_ui(self):
        self.heap_queue = []
        self.projects_list = []
        self.treeview.update(False)

    def de_pickle_session(self):
        try:
            with open("object.pickle", "rb") as f:
                stored_data = pickle.load(f)
                if stored_data is not None:
                    for saved_session in stored_data.stored_sessions:
                        if self.active_session.host == saved_session.host:
                            self.heap_queue = saved_session.heap_queue
                            self.projects_list = saved_session.projects_list
                self.treeview.update()
        except EOFError:
            pass
        self.progress.step(9.99)

    def count_projects(self):
        self.project_counter = {"Completed": 0,
                                "Saved": 0,
                                "Canceled": 0,
                                "Running": 0,
                                "Permission Denied": 0,
                                "Stopping": 0,
                                "Queued": 0}
        for obj in self.projects_list:
            self.project_counter[obj.status] +=1
        self.completed_val.config(text=str(self.project_counter['Completed']))
        self.error_val.config(text=str(
            self.project_counter['Canceled']
            + self.project_counter['Permission Denied']))
        self.warning_val.config(text=str(int(self.project_counter['Saved'])+int(self.project_counter["Stopping"])))
        self.info_val.config(text=str(self.project_counter['Queued']+int(self.project_counter['Running'])))

    def unpickle_creds(self):
        if not os.path.exists('object.pickle'):
            open('object.pickle', 'w+')
        try:
            with open("object.pickle", "rb") as r:
                stored_data = pickle.load(r)
        except EOFError:
            with open("object.pickle", "wb") as w:
                pickle.dump(None, w)
            stored_data = None
        if stored_data is not None:
            self.last_session = SessionConfig(stored_data.last_session)
            self.last_session_exist = stored_data.last_session_exist
        else:
            self.last_session = SessionConfig(None)
            self.last_session_exist = False
        self.active_session = self.last_session

    def pickle_creds(self):
            with open("object.pickle", "rb") as r:
                saved_sessions = pickle.load(r)
            if saved_sessions is None:
                with open("object.pickle", "wb") as w:
                    pickle.dump(SessionSaver([self.active_session.host,
                                              self.active_session.user,
                                              self.active_session.password],
                                             []),
                                w)
                return
            else:
                saved_sessions.last_session = [self.active_session.host,
                                               self.active_session.user,
                                               self.active_session.password]
                with open("object.pickle", "wb") as w:
                    pickle.dump(saved_sessions, w)

    def pickle_session(self):
        if not self.queue_running and\
                not self.treeview.project_running():
            with open("object.pickle", "rb") as r:
                session_saver = pickle.load(r)
                r.close()
            saved = False
            for session_saved in session_saver.stored_sessions:
                if session_saved.host == self.active_session.host:
                    session_saved.heap_queue = self.heap_queue
                    session_saved.projects_list = self.projects_list
                    saved = True
            if not saved:
                session_saver.stored_sessions.append(SessionData(self.active_session.host,
                                                                 self.heap_queue,
                                                                 self.projects_list))
            with open("object.pickle", "wb") as w:
                pickle.dump(session_saver, w)
                w.close()
        elif self.queue_running:
            messagebox.showwarning("Warning", "Stop the queue before disconnecting.")
        else:
            messagebox.showwarning("Warning", "Wait for project to stop running disconnecting.")

    @staticmethod
    def ask_exit():
        result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
        if result == 'yes':
            sys.exit
        else:
            return

    def count_queued_project(self):
        return len(self.heap_queue) + 1

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

    def is_repeated(self, data):
        for obj in self.projects_list:
            if obj.name == data:
                return True
        return False


