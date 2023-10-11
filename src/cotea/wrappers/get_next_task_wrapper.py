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
        self.adding_last_task_after_new = True

        self.new_task_to_add = False
        self.play_iterator = None
        self.strategy_obj = None
        self.new_task = None

        self.should_ignored_errors_uuids = []
        self.should_ignored_unrch_uuids = []

        self.progress_bar = progress_bar


    def __call__(self, real_obj, hosts_left, iterator):
        result = None
        self.strategy_obj = real_obj
        self.play_iterator = iterator

        self.hosts_left = real_obj.get_hosts_left(iterator)

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

            self.should_ignored_errors_uuids = []
            self.should_ignored_unrch_uuids = []
                        
        for hosttask in result:
            if hosttask[TASK_IND]:
                # if we rerun the task or add the new one,
                # the list of already ignored tasks should stay the same
                if not self.rerun_last_task and not self.new_task_to_add:
                    if hosttask[TASK_IND].ignore_errors:
                        if hasattr(hosttask[TASK_IND], "get_name"):
                            if hasattr(hosttask[TASK_IND], "_uuid"):
                                self.should_ignored_errors_uuids.append(hosttask[TASK_IND]._uuid)
                    
                    if hosttask[TASK_IND].ignore_unreachable:
                        if hasattr(hosttask[TASK_IND], "get_name"):
                            if hasattr(hosttask[TASK_IND], "_uuid"):
                                self.should_ignored_unrch_uuids.append(hosttask[TASK_IND]._uuid)

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
        
        if self.new_task_to_add and self.adding_last_task_after_new:
            self.rerun_last_task = True
        else:
            self.rerun_last_task = False

        self.next_task_ignore_errors = False
        self.new_task_to_add = False
        self.adding_last_task_after_new = True
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


    def add_tasks(self, new_tasks):
        if self.strategy_obj and self.play_iterator:
            hosts_left = self.strategy_obj.get_hosts_left(self.play_iterator)

            for host in hosts_left:
                self.play_iterator.add_tasks(host, new_tasks)

            return True, ""
        
        error_msg = "Some of the needed objects are None. Most likely "
        error_msg += "the Ansible execution went further than expected"

        return False, error_msg


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
        skipped_tasks = []
        for host in self.hosts_left:
            host_state_block_and_task = self.play_iterator.get_next_task_for_host(host)
            skipped_task = host_state_block_and_task[len(host_state_block_and_task) - 1]
            skipped_tasks.append(skipped_task)

        skipped_task_name = ""

        if len(skipped_tasks) > 0:
            # task should be tha same on all hosts
            task = skipped_tasks[0]

            if hasattr(task, "get_name"):
                skipped_task_name = str(task.get_name())
        
        return skipped_task_name
    

    def dont_add_last_task_after_new(self):
        self.adding_last_task_after_new = False
