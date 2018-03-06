# External Imports
import base64
import heapq
import threading
from datetime import datetime
from importlib import reload
from tkinter import *
from tkinter import ttk, filedialog, Frame, Label, messagebox, font
import pickle
# Local Imports
import auxiliary_classes
import listbox
import session
import config
from auxiliary_classes import Project


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.master.iconbitmap(r'resources/app_pictogram_orC_icon.ico')
        auxiliary_classes.global_data.session = None
        self.master.withdraw()
        self.enter_credentials_widget()
        self.init_window()
        self.cpu_number = 0
        self.queue_thread = threading.Thread()

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

    def new_connection(self):
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
        settings_frame = Frame(self.master, width=1024, height=32, bg="#3dcd58")
        bottom_frame = Frame(self.master, width=1024, height=570, padx=3, bg="#e0dede")
        queue_frame = Frame(bottom_frame, width=736, height=570, padx=10, borderwidth=1)
        queue_frame.config(relief=RIDGE)
        stats_frame = Frame(bottom_frame, width=288, bg="#e0dede")
        header_frame.pack(fill=BOTH)
        settings_frame.pack(fill=BOTH, expand=True)
        bottom_frame.pack(fill=BOTH, expand=True)
        stats_frame.pack(side=LEFT, padx=16, pady=16, fill=BOTH, expand=True)
        queue_frame.pack(side=RIGHT, padx=16, pady=16, fill=BOTH, expand=True)

        """Declaration of inner frames"""
        # Header_frame needs icon, Name of the Tool, Connection stats, Project completion stats, Disconnect option
        img = PhotoImage(file=r'resources\Header_icon_simq.png')
        icon_frame = Label(header_frame, height=62, width=121, image=img, highlightthickness=0, borderwidth=0)
        icon_frame.photo = img
        icon_frame.pack(side=LEFT, fill=BOTH)
        disconnect_button = Button(header_frame, text="Disconnect", fg="#42b4e6", font=("Arial", 11)
                                   ,command=self.new_connection)
        disconnect_button.config(relief=FLAT, padx=3)
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
        status_frame.pack(fill=BOTH, pady=(0, 8))
        cpu_frame.pack(fill=BOTH, pady=8)
        ram_frame.pack(fill=BOTH, pady=8)
        disk_frame.pack(fill=BOTH, pady=8)

        # queue_frame will have 3 frames, one for header text,
        # one for processing of tasks, one for listbox and one for two buttons
        header_listbox = Frame(queue_frame, width=664, height=100)
        aux_frame = Frame(header_listbox, height=50, pady=5)
        aux_frame.pack(fill=BOTH, expand=True)
        img = PhotoImage(file=r'resources\simulation_queue.png')
        icon_frame = Label(aux_frame, height=19, width=186, image=img, highlightthickness=0, borderwidth=0)
        icon_frame.photo = img
        icon_frame.pack(anchor="w", padx=5, pady=5)
        ttk.Separator(aux_frame, orient=HORIZONTAL).pack(fill=X, expand=True)
        progress_frame = Frame(header_listbox, height=10, pady=5)
        progress_frame.pack(fill=BOTH)
        s = ttk.Style()
        s.configure("red.Horizontal.TProgressbar", foreground='green', background='#3dcd58', theme="alt")
        auxiliary_classes.global_data.progress_queue = ttk.Progressbar(progress_frame, style="red.Horizontal.TProgressbar", orient="horizontal", length=600, mode="determinate",
                        maximum=4, value=1)
        # auxiliary_classes.global_data.progress_queue = ttk.Progressbar(progress_frame, style='Kim.TButton', length=100,
        #                                                                value=0)
        auxiliary_classes.global_data.progress_queue.pack(fill=X)

        listbox_frame = Frame(queue_frame, width=664, height=208)
        bottom_frame = Frame(queue_frame, width=830, height=50, pady=5)
        header_listbox.pack(fill=BOTH, expand=True)
        listbox_frame.pack(fill=BOTH, expand=True)
        bottom_frame.pack(fill=BOTH, expand=True)
        auxiliary_classes.global_data.my_list = listbox.DDList(listbox_frame, height=6)

        # Configuring Connection frame
        img = PhotoImage(file=r'resources\User_picto.png')
        icon_frame = Label(connection_frame, image=img, highlightthickness=0, borderwidth=0)
        icon_frame.photo = img
        icon_frame.pack(side=LEFT, anchor="e")
        auxiliary_classes.global_data.iplabel = Label(connection_frame, text=config.host, fg="#3dcd58",
                                                      font=("Arial", 11, "bold"))
        auxiliary_classes.global_data.iplabel.pack(side=RIGHT, anchor="w")
        # Label(connection_frame, text="Queue Status:").grid(row=2, column=0, sticky=W)
        # auxiliary_classes.global_data.status_queue_label = Label(connection_frame, text="Stopped", foreground="red")

        # Config Status Frame
        status_frame
        status_header = Frame(status_frame, width=256, height=28)
        status_header.pack(side=TOP, fill=BOTH)
        status_body = Frame(status_frame, width=256, height=100)
        status_body.pack(side=BOTTOM, fill=BOTH, expand=True)
        status_body_left = Frame(status_body, width=128, height=100, bg="#e8e8e8")
        status_body_left.pack(side=LEFT, fill=BOTH, expand=True)
        status_body_right = Frame(status_body, width=128, height=100, bg="#e8e8e8")
        status_body_right.pack(side=RIGHT, fill=BOTH, expand=True)
        status_tag = Frame(status_body_left, width=64, height=100, bg="#e8e8e8")
        status_tag.pack(side=TOP, fill=BOTH, expand=True)
        status_val = Frame(status_body_left, width=64, height=100, bg="#e8e8e8")
        status_val.pack(side=BOTTOM, fill=BOTH, expand=True)
        aux_frame = Frame(status_header, width=100, height=10)
        aux_frame.pack(fill=BOTH, expand=True)
        Label(aux_frame, text="Queue Stats", font=("Arial", 10, "bold"), fg="#333333").pack(side=LEFT, padx=3)
        Label(status_tag, text="Completed", font=("Arial", 8), bg="#e8e8e8").pack(side=LEFT, padx=3)
        img = PhotoImage(file=r'resources\completed_picto.png')
        one = Label(status_tag, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=LEFT, padx=3)
        img = PhotoImage(file=r'resources\error_picto.png')
        one = Label(status_tag, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        Label(status_tag, text="Errors", font=("Arial", 8), bg="#e8e8e8").pack(side=RIGHT, padx=3)
        one.pack(side=RIGHT, padx=3)
        img = PhotoImage(file=r'resources\information_picto.png')
        one = Label(status_val, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        Label(status_val, text="Running", font=("Arial", 8), bg="#e8e8e8").pack(side=LEFT, padx=3)
        one.pack(side=LEFT, padx=3)
        Label(status_val, text="Warnings", font=("Arial", 8), bg="#e8e8e8").pack(side=RIGHT, padx=3)
        img = PhotoImage(file=r'resources\warning_picto.png')
        one = Label(status_val, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=RIGHT, padx=3)
        auxiliary_classes.global_data.status_avg = Label(status_body_right, text="--", font=("Arial", 11, "bold"))

        # Configuring Cpu stats frame

        cpu_header = Frame(cpu_frame, width=256, height=28)
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
        img = PhotoImage(file=r'resources\cpu_picto.png')
        aux_frame = Frame(cpu_header, width=100, height=10)
        aux_frame.pack(fill=BOTH, expand=True)
        one = Label(aux_frame, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=LEFT, padx=4)
        Label(aux_frame, text="CPU", font=("Arial", 10, "bold"), fg="#333333").pack(side=LEFT, padx=3)
        ttk.Separator(cpu_header, orient=HORIZONTAL).pack(fill=X, expand=True)
        Label(cpu_tag, text="CPU 0:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.cpu_list[0].pack(fill=BOTH, expand=True, padx=4)
        Label(cpu_tag, text="CPU 1:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.cpu_list[1].pack(fill=BOTH, padx=4, expand=True)
        Label(cpu_tag, text="CPU 2:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.cpu_list[2].pack(fill=BOTH, padx=4, expand=True)
        Label(cpu_tag, text="CPU 3:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.cpu_list.append(Label(cpu_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.cpu_list[3].pack(fill=BOTH, padx=4, expand=True)
        auxiliary_classes.global_data.cpu_avg = Label(cpu_body_right, text="--",
                                                      font=("Arial", 11, "bold"))
        auxiliary_classes.global_data.cpu_avg.pack(side=BOTTOM)
        Label(cpu_body_right, text="USAGE", font=("Arial", 8, "bold"), foreground="gray").pack(side=BOTTOM, pady=(5, 0))

        # Configuring RAM stats frame
        ram_header = Frame(ram_frame, width=256, height=28)
        ram_header.pack(side=TOP, fill=BOTH, pady=3, padx=3)
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
        img = PhotoImage(file=r'resources\ram_picto.png')
        aux_frame = Frame(ram_header, width=100, height=10)
        aux_frame.pack(fill=BOTH)
        one = Label(aux_frame, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=LEFT, padx=4)
        Label(aux_frame, text="RAM", font=("Arial", 10, "bold"), fg="#333333").pack(side=LEFT, padx=3)
        ttk.Separator(ram_header, orient=HORIZONTAL).pack(side=BOTTOM, fill=X, expand=True)
        Label(ram_tag, text="total:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.ram_stats.append(Label(ram_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.ram_stats[0].pack()
        Label(ram_tag, text="used:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.ram_stats.append(Label(ram_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.ram_stats[1].pack()
        Label(ram_tag, text="free:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.ram_stats.append(Label(ram_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.ram_stats[2].pack()
        auxiliary_classes.global_data.ram_stats.append(Label(ram_body_right, text="--",
                                                             font=("Arial", 11, "bold"),
                                                             foreground="green"))
        auxiliary_classes.global_data.ram_stats[3].pack(side=BOTTOM)
        Label(ram_body_right, text="USAGE", font=("Arial", 8, "bold"), foreground="gray").pack(side=BOTTOM)
        # Configuring Disk stats frame

        disk_header = Frame(disk_frame, width=100, height=20)
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

        img = PhotoImage(file=r'resources\disk_picto.png')
        aux_frame = Frame(disk_header, width=100, height=10)
        aux_frame.pack(fill=BOTH)
        one = Label(aux_frame, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=LEFT, padx=4)
        Label(aux_frame, text="DISK", font=("Arial", 10, "bold"), fg="#333333").pack(side=LEFT, padx=3)
        ttk.Separator(disk_header, orient=HORIZONTAL,).pack(side=BOTTOM, fill=X, expand=True)
        Label(disk_tag, text="total:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.disk_storage.append(Label(disk_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.disk_storage[0].pack()
        Label(disk_tag, text="used:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.disk_storage.append(Label(disk_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.disk_storage[1].pack()
        Label(disk_tag, text="free:", font=("Arial", 8), bg="#e8e8e8").pack()
        auxiliary_classes.global_data.disk_storage.append(Label(disk_val, text="--", font=("Arial", 8), bg="#e8e8e8"))
        auxiliary_classes.global_data.disk_storage[2].pack()
        auxiliary_classes.global_data.disk_storage.append(Label(disk_body_right, text="--", font=("Arial", 11, "bold"),
                                                                foreground="green"))
        auxiliary_classes.global_data.disk_storage[3].pack(side=BOTTOM)
        Label(disk_body_right, text="USAGE", font=("Arial", 8, "bold"), foreground="gray").pack(side=BOTTOM)

        # Defining buttons for queue_frame
        
        auxiliary_classes.global_data.delete_button = ttk.Button(bottom_frame, 
                                                                 text='Delete', 
                                                                 state="disabled", 
                                                                 command=auxiliary_classes.global_data.my_list.delete)
        auxiliary_classes.global_data.delete_button.pack(side=RIGHT, padx=(5, 10))
        ttk.Button(bottom_frame, text='Add', command=self.add_project).pack(side=RIGHT, fill=X, padx=(10, 0))
        auxiliary_classes.global_data.status_button = ttk.Button(bottom_frame, 
                                                                 text='Start', 
                                                                 command=self.toggle_queue_status)
        auxiliary_classes.global_data.status_button.pack(side=LEFT, padx=(10, 0))

        # Config of frames
        stats_frame.grid_propagate(False)
        cpu_frame.grid_propagate(False)
        ram_frame.grid_propagate(False)
        disk_frame.grid_propagate(False)

    def toggle_queue_status(self):
        if not auxiliary_classes.global_data.queue_running:
            print(auxiliary_classes.global_data.heap_queue)
            auxiliary_classes.global_data.queue_running = True
            auxiliary_classes.global_data.status_button.config(text="Stop Queue")
            # auxiliary_classes.global_data.status_queue_label.config(text="Running", foreground="green")
            if not self.queue_thread.isAlive():
                self.queue_thread = threading.Thread(target=self.start_queue)
                self.queue_thread.start()
        else:
            auxiliary_classes.global_data.queue_running = False
            auxiliary_classes.global_data.status_button.config(text="Start Queue")
            # auxiliary_classes.global_data.status_queue_label.config(text="Stopped", foreground="red")

    def add_project(self):
        reload(config)
        target_path = f"\\\\{config.host}\\Projects"
        file_path = filedialog.askopenfilename(parent=auxiliary_classes.root, 
                                               filetypes=(("Script Files", "*.SCRIPT"), ("All Files", "*.*")), 
                                               initialdir=target_path, 
                                               title='Please select a .SCRIPT project')
        if len(file_path) > 0:
            self.add_to_queue(file_path)

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
            auxiliary_classes.global_data.session.start_threads()
            self.cpu_number = auxiliary_classes.global_data.session.get_cpu_num()
            auxiliary_classes.global_data.button2.config(state="normal")
            auxiliary_classes.global_data.button1.config(state="normal")
            self.de_pickle_session()
            self.top.destroy()
            self.master.deiconify()

        else:
            self.disconnect()
            auxiliary_classes.global_data.progress.place_forget()
            auxiliary_classes.global_data.msg_refused.place(relx=0.5, rely=0.5, anchor=CENTER)
            auxiliary_classes.global_data.button2.config(state="normal")
            auxiliary_classes.global_data.button1.config(state="normal")
            auxiliary_classes.global_data.progress.config(value=0)
            return

    def enter_credentials_widget(self):
        self.top = Toplevel(self.master)
        self.center(self.top)
        # Removing bordes and adding motion
        self.top.overrideredirect(1)
        self.top.bind("<ButtonPress-1>", self.start_move)
        self.top.bind('<ButtonRelease-1>', self.stop_move)
        self.top.bind("<B1-Motion>", self.on_motion)
        self.top.bind("<Return>", lambda event: self.update_credentials(host.get(),
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
        exit_button.bind('<Button-1>', quit)
        exit_button.pack(side=RIGHT)
        img = PhotoImage(file=r'resources\Cover_Lines.png')
        one = Label(left_frame, image=img, highlightthickness=0, borderwidth=0)
        one.photo = img
        one.pack(side=RIGHT)
        img = PhotoImage(file=r'resources\LIO_SE_195x40.png')
        two = Label(r_footer_frame, image=img)
        two.pack(side=RIGHT, padx=(0, 25))
        two.photo = img
        auxiliary_classes.global_data.progress = ttk.Progressbar(r_loading_frame, length=100, value=0)
        auxiliary_classes.global_data.msg_refused = Label(r_loading_frame,
                                                          text="Connection failed, check credentials and try again.",
                                                          fg="red",
                                                          font=('Arial', 9, 'italic'))
        auxiliary_classes.global_data.msg_entry = Label(r_loading_frame, 
                                                        text="Please, fill all entry fields.", 
                                                        fg="red", 
                                                        font=('Arial', 9, 'italic'))
        host = StringVar(value="Host")
        user = StringVar(value="User")
        password = StringVar(value="Password")
        auxiliary_classes.global_data.checkbox = StringVar()
        self.top.title("Connect to machine")
        self.top.resizable(width=False, height=False)
        # host.set(config.host)
        # user.set(config.user)
        # password.set(base64.b64decode(config.password).decode())

        e1 = ttk.Entry(r_entry_frame, textvariable=host, font=('Arial', 14, 'italic'), foreground="grey")
        e2 = ttk.Entry(r_entry_frame, textvariable=user, font=('Arial', 14, 'italic'), foreground="grey")
        e3 = ttk.Entry(r_entry_frame, textvariable=password, font=('Arial', 14, 'italic'), foreground="grey")
        e3.config(show="*")
        e1.pack(pady=(25, 8))
        e2.pack(pady=8)
        e3.pack(pady=(8, 0))
        check_button = ttk.Checkbutton(
            r_buttons_frame, text="Remember me", variable=auxiliary_classes.global_data.checkbox, onvalue=True)
        check_button.pack(side=TOP, anchor=W, padx=(35, 0), pady=(0, 4))
        imag_last = PhotoImage(file=r'resources\LastSession_button.png')
        auxiliary_classes.global_data.button1 = Button(r_buttons_frame, command=quit)
        auxiliary_classes.global_data.button1.config(image=imag_last, 
                                                     bd=0, width="240", 
                                                     height="32", 
                                                     command=self.update_credentials)
        auxiliary_classes.global_data.button1.photo = imag_last
        login_img = PhotoImage(file=r'resources\Login_button.png')
        auxiliary_classes.global_data.button2 = Button(r_buttons_frame, 
                                                       text="Connect", 
                                                       command=lambda: self.update_credentials(host.get(), 
                                                                                               user.get(), 
                                                                                               password.get()))
        auxiliary_classes.global_data.button2.config(image=login_img, bd=0, width="240", height="32")
        auxiliary_classes.global_data.button2.photo = login_img
        auxiliary_classes.global_data.button2.pack(pady=5)
        auxiliary_classes.global_data.button1.pack(pady=8)

    def update_credentials(self, host=config.host, 
                           user=config.user, 
                           password=base64.b64decode(config.password).decode()):
        # First update the credentials of the config file.
        auxiliary_classes.global_data.msg_refused.place_forget()
        auxiliary_classes.global_data.msg_entry.place_forget()
        auxiliary_classes.global_data.button2.config(state="disabled")
        auxiliary_classes.global_data.button1.config(state="disabled")
        if host == "Host" or host == "":
            auxiliary_classes.global_data.msg_entry.place(relx=0.5, rely=0.5, anchor=CENTER)
            auxiliary_classes.global_data.button2.config(state="normal")
            auxiliary_classes.global_data.button1.config(state="normal")
            return
        if auxiliary_classes.global_data.checkbox:
            if not password == base64.b64decode(config.password).decode():
                encoded_password = base64.b64encode(password.encode())
            else:
                encoded_password = config.password
            with open("config.py", "w") as sf:
                sf.write(f"host = \"{host}\" \nuser = \"{user}\" \npassword = {encoded_password}")
            reload(config)
        auxiliary_classes.global_data.progress.place(relx=0.5, rely=0.5, anchor=CENTER)
        auxiliary_classes.global_data.session = session.Session(config.host, 
                                                                config.user, 
                                                                base64.b64decode(config.password).decode())
        auxiliary_classes.global_data.host = config.host
        auxiliary_classes.global_data.progress.step(30)
        t = threading.Thread(target=self.connect_via_ssh)
        t.start()
        auxiliary_classes.global_data.iplabel.config(text=host)

    def disconnect(self):
        # STOP QUEUE
        self.pickle_session()
        auxiliary_classes.global_data.queue_running = False
        auxiliary_classes.global_data.status_button.config(text="Start Queue")
        # SESSION OFF
        auxiliary_classes.global_data.session.flag_stop = True
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
            auxiliary_classes.global_data.my_list.update()
        except EOFError:
            pass
        auxiliary_classes.global_data.progress.step(9.99)

    @staticmethod
    def pickle_session():
        if not auxiliary_classes.global_data.queue_running and\
                not auxiliary_classes.global_data.my_list.project_running():
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
                    [auxiliary_classes.global_data.host,
                     auxiliary_classes.global_data.heap_queue,
                     auxiliary_classes.global_data.projects_queue,
                     auxiliary_classes.global_data.data_table])
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
