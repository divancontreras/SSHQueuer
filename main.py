from tkinter import *

DUMMY_NAMES = ['termo_1_dumy','lorem_ipsum_@', 'just_another', 'testing_this23', 'more_testing']

class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.init_window()

    def donothing(self):
        filewin = Toplevel(self.master)
        button = Button(filewin, text="Do nothing button")
        button.pack()

    def init_window(self):
        self.master.title("Queue")
        Label(self.master, text="Queuer of Simulations").pack()
        Label(self.master, text="Current IP:").pack()
        self.master.geometry("300x300")

        menubar = Menu(self.master)
        # create a pulldown menu, and add it to the menu bar
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Connection", command=self.donothing)
        filemenu.add_command(label="Open target folder", command=self.donothing)
        filemenu.add_command(label="Open SSH", command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.master.config(menu=menubar)
        length = 10
        dd = DDList(self.master, height=length)
        dd.pack()
        for i in range(len(DUMMY_NAMES)):
            dd.insert(END, DUMMY_NAMES[i])
        Button(self.master, text='Add', command=self.donothing).pack(side=LEFT, anchor=W, fill=X, expand=YES)
        Button(self.master, text='Resume', command=self.donothing).pack(side=LEFT, anchor=W, fill=X, expand=YES)
        Button(self.master, text='Pause', command=self.donothing).pack(side=LEFT, anchor=W, fill=X, expand=YES)



class DDList(Listbox):
    """ A Tkinter listbox with drag'n'drop reordering of entries. """
    def __init__(self, master, **kw):
        kw['selectmode'] = SINGLE
        Listbox.__init__(self, master, kw)
        self.pack(fill=BOTH, expand=2)
        self.bind('<Button-1>', self.set_current)
        self.bind('<B1-Motion>', self.shift_selection)
        self.curIndex = None

    def set_current(self, event):
        self.curIndex = self.nearest(event.y)

    def shift_selection(self, event):
        i = self.nearest(event.y)
        if i < self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.curIndex = i


root = Tk()
app = Window(root)
root.mainloop()

