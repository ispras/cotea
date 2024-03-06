class ansible_progress_bar:
    def __init__(self):
        self.executed_count = 0
        self.bar_len = 100
        self.bar_sym = u"█"
        self.bar_empty_sym = "."
        self.total_task_count = -1
    

    def set_total_task_count(self, tasks_count):
        self.total_task_count = tasks_count
    
    def update(self):
        self.executed_count += 1


    def add_to_total_task_count(self, num):
        self.total_task_count += num


    def print_bar(self, play_name, task_name):
        if self.total_task_count <= 0:
            return
        
        try:
            percent = self.executed_count / self.total_task_count
        except ZeroDivisionError as e:
            return

        divisions = int(percent * self.bar_len)
        if divisions > self.bar_len:
            divisions = self.bar_len

        if divisions < 0:
            divisions = 0
        
        divisions_str = self.bar_sym*divisions

        percent = percent * 100
        empty_divisions = self.bar_empty_sym*(self.bar_len - divisions)

        bar = "Next task: {}. Play: {}\n[{}{}]  {} / {}, {:.2f}%".format(task_name,
                                                                       play_name,
                                                                       divisions_str,
                                                                       empty_divisions,
                                                                       self.executed_count,
                                                                       self.total_task_count,
                                                                       percent)
        
        print(bar, "\n")

