# External Imports
from tkinter.font import Font
from tkinter import ttk, messagebox
from tkinter import *
import heapq
# Local Imports
import main


class DDList:
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
            main.global_data.delete_button.config(state="normal")
        else:
            main.global_data.delete_button.config(state="disabled")

    def b_move(self, event):
        moveto = self.tree.index(self.tree.identify_row(event.y))
        if main.global_data.queue_running and (moveto == 0 or self.tree.index(self.tree.selection()) == 0):
            return
        for s in self.tree.selection():
            self.tree.move(s, '', moveto)
        self.moved_flag = True

    def do_kill_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        main.global_data.session.kill_process(name)

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
        for obj in main.global_data.projects_queue:
            if obj.name == name:
                if obj.status == "Running":
                    path = obj.bash_path
                    obj.status = "Stopping"
                    main.global_data.my_list.update()
                else:
                    return
        main.global_data.session.stop_process(path)

    def update(self, refill=True):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if refill:
            for obj in main.global_data.projects_queue:
                main.global_data.my_list.insert(obj.get_list())
            self._column_sort("Turn", False)
        if not len(main.global_data.heap_queue) > 0:
            main.global_data.status_button.config(state="disabled")
        else:
            main.global_data.status_button.config(state="normal")

    def project_running(self):
        is_running = False
        for listbox_entry in self.tree.get_children():
            for proj in main.global_data.projects_queue:
                if proj.name == self.tree.item(listbox_entry)['values'][0]:
                    if proj.status == "Running":
                        is_running = True
        return is_running

    def adjust_queue_turn(self):
        turn = 0
        aux_list = []
        for listbox_entry in self.tree.get_children():
            for proj in main.global_data.projects_queue:
                if proj.name == self.tree.item(listbox_entry)['values'][0]:
                    if proj.status == "Running" or proj.status == "Queued":
                        turn += 1
                        heapq.heappush(aux_list, [int(turn), self.tree.item(listbox_entry)['values'][0]])
                        proj.turn = turn
        main.global_data.heap_queue = aux_list

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

    def delete(self, event=None):
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
        main.global_data.delete_button.config(state="disabled")

    def remove_from_queue(self, data, item):
        aux_list = []
        self.tree.delete(item)

        # REMOVE FROM THE LIST OF PROJECT OBJECTS
        for obj in main.global_data.projects_queue:
            if obj.name == data:
                main.global_data.projects_queue.remove(obj)

        # REMOVE FROM THE ACTUAL QUEUE
        for element in main.global_data.heap_queue:
            if element[1] != data:
                heapq.heappush(aux_list, element)
        main.global_data.heap_queue = aux_list

    def _load_data(self):
        # configure column headings
        for c in self.dataCols:
            self.tree.heading(c, text=c.title())
            # command=lambda c=c: self._column_sort(c, self.SortDir)
            self.tree.column(c, width=Font().measure(c.title()))

        # add data to the tree
        for item in main.global_data.data_table:
            self.tree.insert('', 'end', values=item)

            # and adjust column widths if necessary
            for idx, val in enumerate(item):
                iwidth = Font().measure(val)
                if self.tree.column(self.dataCols[idx], 'width') < iwidth:
                    self.tree.column(self.dataCols[idx], width=iwidth)

    def _column_sort(self, col, descending=False):
        # The sort it's forced to the column!
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

    @staticmethod
    def element_running(data):
        for obj in main.global_data.projects_queue:
            if obj.name == data:
                if obj.status == "Running":
                    return True
                else:
                    return False
