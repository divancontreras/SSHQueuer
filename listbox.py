# External Imports
from tkinter.font import Font
from tkinter import ttk, messagebox
from tkinter import *
import heapq
from operator import attrgetter
# Local Imports

class DDList:
    """ A Tkinter listbox with drag'n'drop reordering of entries. """

    def __init__(self, master, widgets,**kw):
        self.widgets = widgets
        self.SortDir = True
        f = ttk.Frame(master)
        f.pack(fill=BOTH, expand=True)
        self.dataCols = ('Project Name', 'Status', 'Cores', 'Added date/time')
        self.tree = ttk.Treeview(columns=self.dataCols)
        self.mouse_event = None
        self.moved_flag = False
        self.img_container = {}
        self.popup_menu = Menu(master, tearoff=0)
        self.popup_menu.add_command(label="Delete",
                                    command=lambda: self.delete(self.mouse_event))
        self.popup_menu.add_command(label="Save",
                                    command=lambda: self.do_stop_process(self.mouse_event))
        self.popup_menu.add_command(label="Cancel",
                                    command=lambda: self.do_kill_process(self.mouse_event))
        # self.popup_menu.add_command(label="Pause",
        #                             command=lambda: self.do_pause_process(self.mouse_event))
        # self.popup_menu.add_command(label="Resume",
        #                             command=lambda: self.do_resume_process(self.mouse_event))
        self.tree.grid(in_=f, row=0, column=0, sticky=NSEW)
        self.tree.heading('#0', anchor='center')
        self.tree.heading('#1', text='Project Name', anchor='center')
        self.tree.heading('#2', text='Status', anchor='center')
        self.tree.heading('#3', text='Cores', anchor='center')
        self.tree.heading('#4', text='Added date/time', anchor='center')
        self.tree.column('#0', anchor='center', width=1)
        self.tree.column('#1', anchor='w')
        self.tree.column('#2', anchor='center')
        self.tree.column('#3', anchor='center')
        self.tree.column('#4', anchor='center')
        # set frame resize priorities
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)
        style = ttk.Style()
        style.layout("Treeview.Item",
                     [('Treeitem.padding', {'sticky': 'nswe', 'children':
                         [('Treeitem.indicator', {'side': 'left', 'sticky': ''}),
                          ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                          # ('Treeitem.focus', {'side': 'left', 'sticky': '', 'children': [
                          ('Treeitem.text', {'side': 'left', 'sticky': ''}),
                          # ]})
                          ],
                                            })]
                     )
        style.configure('Treeview', rowheight=38)
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
            # self.update()
            self.moved_flag = False
        if len(self.tree.selection()) > 0:
            self.widgets.delete_button.config(state="normal")
        else:
            self.widgets.delete_button.config(state="disabled")

    def b_move(self, event):
        moveto = self.tree.index(self.tree.identify_row(event.y))
        if self.widgets.queue_running and (moveto == 0 or self.tree.index(self.tree.selection()) == 0):
            return
        for s in self.tree.selection():
            self.tree.move(s, '', moveto)
        self.moved_flag = True

    def do_kill_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        self.widgets.session.kill_process(name)

    def do_stop_process(self, event):
        item = self.tree.identify('item', event.x, event.y)
        name = self.tree.item(item)['values'][0]
        for obj in self.widgets.projects_list:
            if obj.name == name:
                if obj.is_running():
                    path = obj.bash_path
                    obj.set_stopping()
                    self.update()
                else:
                    return
        self.widgets.session.stop_process(path)

    def update(self, refill=True):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.widgets.count_projects()
        if refill:
            if len(self.widgets.projects_list) > 0:
                self.widgets.projects_list.sort(key=attrgetter('turn'))
            for item in self.widgets.projects_list:
                self.insert(item)
        if not len(self.widgets.heap_queue) > 0:
            self.widgets.status_button.config(state="disabled")
        else:
            self.widgets.status_button.config(state="normal")


    def project_running(self):
        is_running = False
        for listbox_entry in self.tree.get_children():
            for proj in self.widgets.projects_list:
                if proj.name == self.tree.item(listbox_entry)['values'][0]:
                    if proj.is_running():
                        is_running = True
        return is_running

    def adjust_queue_turn(self):
        turn = 0
        aux_list = []
        for listbox_entry in self.tree.get_children():
            for proj in self.widgets.projects_list:
                if proj.name == self.tree.item(listbox_entry)['values'][0]:
                    if proj.is_running() or proj.is_queued():
                        turn += 1
                        heapq.heappush(aux_list, [int(turn), self.tree.item(listbox_entry)['values'][0]])
                        proj.turn = turn
        self.widgets.heap_queue = aux_list

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

    def insert(self, obj):
        self.img_container[obj.name] = PhotoImage(file=obj.img)
        self.tree.insert('', 'end', image=self.img_container[obj.name],
                         value=obj.get_list())

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
        else:
            messagebox.showwarning("Warning", "You can't delete a project that is running!")
        self.widgets.delete_button.config(state="disabled")

    def remove_from_queue(self, data, item):
        aux_list = []
        self.tree.delete(item)

        # REMOVE FROM THE LIST OF PROJECT OBJECTS
        for obj in self.widgets.projects_list:
            if obj.name == data:
                self.widgets.projects_list.remove(obj)

        # REMOVE FROM THE ACTUAL QUEUE
        for element in self.widgets.heap_queue:
            if element[1] != data:
                heapq.heappush(aux_list, element)
        self.widgets.heap_queue = aux_list

    def _load_data(self):
        # configure column headings
        for c in self.dataCols:
            self.tree.heading(c, text=c.title())
            # command=lambda c=c: self._column_sort(c, self.SortDir)
            self.tree.column(c, width=Font().measure(c.title()))

        # add data to the tree
        for obj in self.widgets.projects_list:
            self.img_container[obj.name] = PhotoImage(file=obj.img)
            self.tree.insert('', 'end', image=self.img_container[obj.name],
                             value=obj.get_list())
            # and adjust column widths if necessary
            for idx, val in enumerate(obj):
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

    def element_running(self, data):
        for obj in self.widgets.projects_list:
            if obj.name == data:
                if obj.is_running():
                    return True
                else:
                    return False

