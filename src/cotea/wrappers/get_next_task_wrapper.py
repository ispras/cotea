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
        self.run_last_one = False
        self.next_task_ignore_errors = False
        self.show_progress_bar = show_progr_bar

        self.already_ignore_failed = []
        self.already_ignore_unrch = []

        self.progress_bar = progress_bar


    def __call__(self, real_obj, hosts_left, iterator):
        result = None

        if self.run_last_one:
            self._copy_prev_tasks(self.prev_tasks)
            result = self.next_tasks
        else:
            self._copy_prev_tasks(self.next_tasks)
            result = self.func(real_obj, hosts_left, iterator)
            self.next_tasks = result

            self.already_ignore_failed = []
            self.already_ignore_unrch = []
        
        for hosttask in result:
            if hosttask[TASK_IND]:
                # if we rerun the task, the list of already ignored tasks
                # should stay the same
                if not self.run_last_one:
                    if hosttask[TASK_IND].ignore_errors:
                        if hasattr(hosttask[TASK_IND], "get_name"):
                            self.already_ignore_failed.append(str(hosttask[TASK_IND].get_name()))
                    
                    if hosttask[TASK_IND].ignore_unreachable:
                        if hasattr(hosttask[TASK_IND], "get_name"):
                            self.already_ignore_unrch.append(str(hosttask[TASK_IND].get_name()))

                if self.next_task_ignore_errors:
                    hosttask[TASK_IND].ignore_errors = True
                    hosttask[TASK_IND].ignore_unreachable = True
        
        self.run_last_one = False
        self.next_task_ignore_errors = False

        if self.get_next_task_name() is not None:
            self.progress_bar.update()
            
            if self.show_progress_bar:
                play_name = iterator._play.get_name()
                self.progress_bar.print_bar(play_name, self.get_next_task_name())

        self.before_task_bp.stop()
        
        '''
        self.logger.info("task run")
        #print(dir(result[0][1]))
        #print(dir(result[0][1]._name))
        if result[0][1] != None:
            if result[0][1].name == "Execute bad command":
                self.zapas_task = result[0][1].copy()
        else:
            if self.zapas_task != None:
                print("aaaaa")
                return [(result[0][0], self.zapas_task)]
        #self.sync_obj.continue_runner_with_stop()

        print("zapas:", type(self.zapas_task))
        '''

        return result

        # все следующие - meta -> прокручиваем их без стопа и без
        #                         возврата управления
        # следующий - норм таск -> возвращаем управление, говоря true
        # следующих не осталось -> возвращаем управление, говоря false


    def _copy_prev_tasks(self, hosttasks):
        self.prev_tasks = []

        for hosttask in hosttasks:
            temp_host = None
            temp_task = None

            if hosttask[HOST_IND]:
                temp_host = Host()
                temp_host.deserialize(hosttask[HOST_IND].serialize())
            
            if hosttask[TASK_IND]:
                temp_task = hosttask[TASK_IND].copy()

            if temp_host:
                self.prev_tasks.append( (temp_host, temp_task) )


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