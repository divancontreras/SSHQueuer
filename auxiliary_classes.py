
class Project():
    def __init__(self, name, img, path, cores, status, turn, added_time):
        self.name = name
        self.img = img
        self.path = path
        self.turn = turn
        self.cores = cores
        self.status = status
        self.added_time = added_time

    def is_running(self):
        return self.status == "Running"

    def is_queued(self):
        return self.status == "Queued"

    def set_saved(self):
        self.status = "Saved"
        self.img = "resources\warning_picto.png"

    def set_running(self):
        self.status = "Running"

    def set_stopping(self):
        self.status = "Stopping"
        self.img = "resources\warning_picto.png"

    def set_canceled(self):
        self.status = "Canceled"
        self.img = "resources\error_picto.png"

    def set_denied(self):
        self.status = "Permission Denied"
        self.img = "resources\error_picto.png"

    def set_completed(self):
        self.status = "Completed"
        self.img = "resources\completed_picto.png"

    def get_list(self):
        return self.name, self.status, self.cores, self.added_time


class SessionSaver:
    def __init__(self, creds=None, session=None, last_session_exist=False):
        if creds:
            self.last_session = creds
        else:
            self.last_session = []
        if session:
            self.stored_sessions = session
        else:
            self.stored_sessions = []
        self.last_session_exist = last_session_exist

class SessionData:
    def __init__(self, host, heap_queue, projects_list):
        self.host = host
        self.heap_queue = heap_queue
        self.projects_list = projects_list

class SessionConfig:
    def __init__(self, data_list):
        if data_list != [] and data_list is not None:
            self.host = data_list[0]
            self.user = data_list[1]
            self.password = data_list[2]
        else:
            self.host = ""
            self.user = ""
            self.password = ""
