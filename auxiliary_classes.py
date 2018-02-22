class Project():
    def __init__(self, name, path, cores, status, turn, added_time):
        self.name = name
        self.path = path
        self.turn = turn
        self.cores = cores
        self.status = status
        self.added_time = added_time

    def get_list(self):
        return (self.name, self.status, self.cores, self.turn, self.added_time)

class GUIData:
    def __init__(self, user, host):
        self.user = user
        self.host = host
        self.load = False
        self.connection_exist = False
        self.cpu_list = []
        self.data_table = []
        self.heap_queue = []
        self.projects_queue = []
        self.name_pid = {}
        self.name_mpid = {}
        self.ram_stats = []
        self.disk_storage = []
        self.queue_running = False
        self.task_stopped = False
        self.task_canceled = False
