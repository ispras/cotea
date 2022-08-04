PLAY_NAME_IND = 0
PLAY_TASKS_IND = 1

class AnsibleExecTree:
    def __init__(self):
        self.tree = []
        #self.hosts_tasks = {}
        self.task_count = -1
    

    def add_play(self, play_name):
        play_exist = False
        for play in self.tree:
            if play[PLAY_NAME_IND] == play_name:
                play_exist = True
                break
        
        if not play_exist:
            self.tree.append([play_name, {}])
    

    def add_task(self, play_name, host_name, task_name):
        added = False

        for play in self.tree:
            if play[PLAY_NAME_IND] == play_name:
                if host_name not in play[PLAY_TASKS_IND]:
                    play[PLAY_TASKS_IND][host_name] = []

                play[PLAY_TASKS_IND][host_name].append(task_name)
                added = True

                '''
                if host_name not in self.hosts_tasks:
                    self.hosts_tasks[host_name] = []
                
                self.hosts_tasks[host_name].append(task_name)
                '''

                break
    

    def compute_metrics(self):
        self.task_count = 0

        for play in self.tree:
            tmp_max = -1

            for host in play[PLAY_TASKS_IND]:
                tmp_max = max(tmp_max, len(play[PLAY_TASKS_IND][host]))
            
            self.task_count += tmp_max


    def pretty_print(self):
        for play in self.tree:
            print("Play name:", play[PLAY_NAME_IND])
            
            for host_name in play[PLAY_TASKS_IND]:
                print("Host name:", host_name)
                print(play[PLAY_TASKS_IND][host_name], "\n")
            
            print("\n")
        
        print("Task count -", self.task_count)

