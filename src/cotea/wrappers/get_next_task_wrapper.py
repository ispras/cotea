from ansible.inventory.host import Host

from cotea.wrappers.wrapper_base import wrapper_base
from cotea.wrappers.ansi_breakpoint import ansi_breakpoint

HOST_IND = 0
TASK_IND = 1


# wraps ansible.plugins.strategy.linear.StrategyModule._get_next_task_lockstep()
class get_next_task_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger, bp_label):
        super().__init__(func, sync_obj, logger)
        self.before_task_bp = ansi_breakpoint(sync_obj, bp_label)
        self.prev_tasks = []
        self.next_tasks = []
        self.run_last_one = False


    def __call__(self, real_obj, hosts_left, iterator):
        result = None

        if self.run_last_one:
            result = self.prev_tasks
            self.run_last_one = False
        else:
            result = self.func(real_obj, hosts_left, iterator)

        self._copy_prev_tasks(result)
        self.next_tasks = result
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