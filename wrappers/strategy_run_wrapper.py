from ansirate.wrappers.wrapper_base import wrapper_base


# wraps ansible.plugins.strategy.linear.StrategyModule.run()
class strategy_run_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)

        self.cur_play_hosts_tasks = {}
        self.total_tasks_count = 0
        self.ansible_iterator = None
        self.ansible_play_context = None
        self.hosts_left = None

    def __call__(self, real_obj, iterator, play_context):
        self.logger.debug("WRAPPER: BEFORE RUN")
        real_obj._set_hosts_cache(iterator._play)
        self.hosts_left = real_obj.get_hosts_left(iterator)
        prev_host_states = iterator._host_states.copy()
        real_task_ind = 1
        self.cur_play_hosts_tasks = {}

        for host in self.hosts_left:
            self.cur_play_hosts_tasks[host] = []
            while True:
                task = iterator.get_next_task_for_host(host)
                if task[real_task_ind] is None:
                    break
                self.cur_play_hosts_tasks[host].append(task[real_task_ind])

            # moving iterator to start state
            try:
                prev_host_state = prev_host_states[host.name]
            except KeyError:
                prev_host_state = iterator.get_host_state(host)
            iterator._host_states[host.name] = prev_host_state

        self.ansible_iterator = iterator
        self.ansible_play_context = play_context

        # flashing control to runner
        self.sync_obj.continue_runner_with_stop()

        result = self.func(real_obj, iterator, play_context)
        return result
