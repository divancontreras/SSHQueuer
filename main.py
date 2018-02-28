# Local Imports
import auxiliary_classes
# External Imports
from tkinter import messagebox
import pickle
import window


def on_closing():
    result = messagebox.askquestion("Exit", "Are  you sure you want to exit?", icon='warning')
    if result == 'yes':
        pass
    else:
        return
    if not auxiliary_classes.global_data.queue_running and not auxiliary_classes.global_data.my_list.project_running():
        with open("object.pickle", "rb") as r:
            stored_data = pickle.load(r)
        saved = False
        for session_saved in stored_data:
            if session_saved[0] == auxiliary_classes.global_data.host:
                session_saved[1] = auxiliary_classes.global_data.heap_queue
                session_saved[2] = auxiliary_classes.global_data.projects_queue
                session_saved[3] = auxiliary_classes.global_data.data_table
                saved = True
        if not saved:
            stored_data.append([auxiliary_classes.global_data.host, auxiliary_classes.global_data.heap_queue, auxiliary_classes.global_data.projects_queue, auxiliary_classes.global_data.data_table])
        with open("object.pickle", "wb") as w:
            pickle.dump(stored_data, w)
        if auxiliary_classes.global_data.connection_exist:
            auxiliary_classes.global_data.session.ssh.close()
        exit()
    elif auxiliary_classes.global_data.queue_running:
        messagebox.showwarning("Warning", "Stop the queue before exiting the program.")
    else:
        messagebox.showwarning("Warning", "Wait for project to stop running before exiting.")


if __name__ == "__main__":
    app = window.Window(auxiliary_classes.root)
    auxiliary_classes.root.protocol("WM_DELETE_WINDOW", on_closing)
    auxiliary_classes.root.mainloop()
