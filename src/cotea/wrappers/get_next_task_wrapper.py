from ansible.inventory.host import Host

from cotea.wrappers.wrapper_base import wrapper_base
from cotea.wrappers.ansi_breakpoint import ansi_breakpoint
from cotea.progress_bar import ansible_progress_bar

HOST_IND = 0
TASK_IND = 1


# wraps ansible.plugins.strategy.linear.StrategyModule._get_next_task_lockstep()
class get_next_task_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger, bp_label, progress_bar: ansible_progress_bar, show_progr_bar=False):
        super().__init__(func, sync_obj, logger)
        self.before_task_bp = ansi_breakpoint(sync_obj, bp_label)
        self.prev_tasks = []
        self.next_tasks = []
        self.task_before_new = None
        self.show_progress_bar = show_progr_bar
        self.hosts_left = None

        self.rerun_last_task = False
        self.next_task_ignore_errors = False

        self.new_task_to_add = False
        self.new_task = None

        self.already_ignore_failed = []
        self.already_ignore_unrch = []

        self.progress_bar = progress_bar


    def __call__(self, real_obj, hosts_left, iterator):
        self.hosts_left = real_obj.get_hosts_left(iterator)
        result = None

        if self.new_task_to_add:
            self.task_before_new = self._copy_hosttasks(self.prev_tasks)
            prev_tasks_with_new_task_set = self._set_task_in_hosttasks(self.new_task, self.task_before_new)
            self.next_tasks = prev_tasks_with_new_task_set
            result = prev_tasks_with_new_task_set

        elif self.rerun_last_task:
            if self.task_before_new:
                self.next_tasks = self._copy_hosttasks(self.task_before_new)
                self.task_before_new = None
            else:
                self.next_tasks = self._copy_hosttasks(self.prev_tasks)
            
            result = self.next_tasks

        else:
            result = self.func(real_obj, hosts_left, iterator)
            self.next_tasks = result

            self.already_ignore_failed = []
            self.already_ignore_unrch = []
                        
        for hosttask in result:
            if hosttask[TASK_IND]:
                # if we rerun the task or add the new one,
                # the list of already ignored tasks should stay the same
                if not self.rerun_last_task and not self.new_task_to_add:
                    if hosttask[TASK_IND].ignore_errors:
                        if hasattr(hosttask[TASK_IND], "get_name"):
                            print(hosttask[TASK_IND].ignore_errors)
                            self.already_ignore_failed.append(str(hosttask[TASK_IND].get_name()))
                    
                    if hosttask[TASK_IND].ignore_unreachable:
                        if hasattr(hosttask[TASK_IND], "get_name"):
                            self.already_ignore_unrch.append(str(hosttask[TASK_IND].get_name()))

                if self.next_task_ignore_errors:
                    hosttask[TASK_IND].ignore_errors = True
                    hosttask[TASK_IND].ignore_unreachable = True

        if self.get_next_task_name() is not None:
            self.progress_bar.update()
            
            if self.show_progress_bar:
                play_name = iterator._play.get_name()
                task_name = None
                if self.new_task_to_add:
                    if hasattr(self.new_task, "get_name"):
                        task_name = self.new_task.get_name()
                    else:
                        task_name = self.get_next_task_name()
                else:
                    task_name = self.get_next_task_name()
                    
                self.progress_bar.print_bar(play_name, task_name)
        
        if self.new_task_to_add:
            self.rerun_last_task = True
        else:
            self.rerun_last_task = False

        self.next_task_ignore_errors = False
        self.new_task_to_add = False
        self.new_task = None

        self.before_task_bp.stop()

        return result


    def _copy_hosttasks(self, hosttasks):
        hosttasks_copy = []

        for hosttask in hosttasks:
            temp_host = None
            temp_task = None

            if hosttask[HOST_IND]:
                temp_host = Host()
                temp_host.deserialize(hosttask[HOST_IND].serialize())
            
            if hosttask[TASK_IND]:
                temp_task = hosttask[TASK_IND].copy()

            if temp_host:
                hosttasks_copy.append( (temp_host, temp_task) )
        
        return hosttasks_copy


    def set_next_to_prev(self):
        self.prev_tasks = self._copy_hosttasks(self.next_tasks)
        self.next_tasks = []


    def _set_task_in_hosttasks(self, new_task, hosttasks):
        hosttasks_with_new_task = []

        for hosttask in hosttasks:
            temp_host = None

            if hosttask[HOST_IND]:
                temp_host = Host()
                temp_host.deserialize(hosttask[HOST_IND].serialize())

            if temp_host:
                hosttasks_with_new_task.append( (temp_host, new_task) )
        
        return hosttasks_with_new_task


    def get_next_task(self):
        res = None
        
        if len(self.next_tasks) > 0:
            if len(self.next_tasks[0]) >= 2:
                res = self.next_tasks[0][TASK_IND]

        return res
    

    def get_next_task_name(self):
        res = None 
        next_task = self.get_next_task()

        if next_task:
            res = next_task.get_name()
        
        return res
    

    def get_prev_task(self):
        res = None

        if len(self.prev_tasks) > 0:
            if len(self.prev_tasks[0]) >= 2:
                res = self.prev_tasks[0][TASK_IND]

        return res
    
    
    def get_prev_task_name(self):
        res = None
        prev_task = self.get_prev_task()

        if prev_task:
            res = prev_task.get_name()
        
        return res
    
    
    def skip_next_task(self):
        for host in self.hosts_left:
            self.ansible_iterator.get_next_task_for_host(host)
