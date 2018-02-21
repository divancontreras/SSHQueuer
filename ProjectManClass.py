class ProjectSim():
    def __init__(self, name, path, cores, status, turn, added_time):
        self.name = name
        self.path = path
        self.turn = turn
        self.cores = cores
        self.status = status
        self.added_time = added_time

    def get_list(self):
        return (self.name, self.status, self.cores, self.turn, self.added_time)
