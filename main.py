# Local Imports
import config
from auxiliary_classes import GUIData
#External Imports
from tkinter import messagebox, Tk
import pickle
import window
global global_data
global root
def on_closing():
    result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
    if result == 'yes':
        pass
    else:
        return
    if not global_data.queue_running and not global_data.my_list.project_running():
        with open("object.pickle", "rb") as r:
            stored_data = pickle.load(r)
        saved = False
        for session_saved in stored_data:
            if session_saved[0] == global_data.host:
                session_saved[1] = global_data.heap_queue
                session_saved[2] = global_data.projects_queue
                session_saved[3] = global_data.data_table
                saved = True
        if not saved:
            stored_data.append([global_data.host, global_data.heap_queue, global_data.projects_queue, global_data.data_table])
        with open("object.pickle", "wb") as w:
            pickle.dump(stored_data, w)
        if global_data.connection_exist:
            global_data.session.ssh.close()
        exit()
    elif global_data.queue_running:
        messagebox.showwarning("Warning", "Stop the queue before exiting the program.")
    else:
        messagebox.showwarning("Warning", "Wait for project to stop running before exiting.")


if __name__ == "__main__":
    root = Tk()
    global_data = GUIData(config.user, config.host)
    app = window.Window(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
