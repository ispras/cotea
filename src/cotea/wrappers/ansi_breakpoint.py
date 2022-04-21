class ansi_breakpoint:
    def __init__(self, sync_obj, label):
        self.sync_obj = sync_obj
        self.label = label
    
    def stop(self):
        self.sync_obj.continue_runner_with_stop(self.label)