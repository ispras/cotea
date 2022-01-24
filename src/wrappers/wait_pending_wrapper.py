from cotea.src.wrappers.wrapper_base import wrapper_base


# wraps ansible.plugins.strategy.StrategyBase._wait_on_pending_results()
class wait_pending_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)

        self.results = []
        self.hosts_left = None
        self.ansible_iterator = None
        self.this_is_last_play = False
        self.failed_task = False
        self.unreachable_hosts = []
        self.failed_hosts = []
        self.call_count = 0

    def __call__(self, real_obj, iterator):
        self.logger.debug("WRAPPER: BEFORE COLLECTING")
        self.call_count += 1
        ret_results = self.func(real_obj, iterator)
        self.ansible_iterator = iterator
        self.hosts_left = real_obj.get_hosts_left(iterator)
        self.results.append(ret_results)

        for got_result in ret_results:
            if got_result.is_failed() and not \
                            got_result._task_fields.get('ignore_errors'):
                self.failed_task = True
                self.sync_obj.continue_runner_with_stop()
                return ret_results

        '''
        if self.has_next_task() or not self.this_is_last_play:
            self.sync_obj.continue_runner_with_stop()
        else:
            self.sync_obj.continue_runner()
        '''

        self.sync_obj.continue_runner_with_stop()

        if real_obj._tqm._unreachable_hosts:
            for unrch_host in real_obj._tqm._unreachable_hosts:
                if unrch_host not in self.unreachable_hosts:
                    self.unreachable_hosts.append(unrch_host)

        if real_obj._tqm._failed_hosts:
            for failed_host in real_obj._tqm._failed_hosts:
                if failed_host not in self.failed_hosts:
                    self.failed_hosts.append(failed_host)

        return ret_results

    def print_results(self):
        for res_of_pass in self.results:
            for res in res_of_pass:
                self.logger.info(res._host, end=" | ")
                self.logger.info(res._task)
                # self.logger.debug(res.is_unreachable())
            self.logger.info()

    def has_next_task(self):
        prev_host_states = self.ansible_iterator._host_states.copy()
        hosts_with_next_task = 0
        real_task_ind = 1

        for host in self.hosts_left:
            while True:
                task = self.ansible_iterator.get_next_task_for_host(host)
                if task[real_task_ind]:
                    self.logger.debug("iter -- %s",
                                      task[real_task_ind].get_name())
                    self.logger.debug("name attr = %s",
                                      task[real_task_ind].name)
                    '''
                    hosts_with_next_task += 1
                    break
                    '''
                    if task[real_task_ind].get_name() != "meta":
                        hosts_with_next_task += 1
                        break
                else:
                    break

            # moving iterator to start state
            try:
                prev_host_state = prev_host_states[host.name]
            except KeyError:
                prev_host_state = self.ansible_iterator.get_host_state(host)
            self.ansible_iterator._host_states[host.name] = prev_host_state

        if hosts_with_next_task > 0:
            # return hosts_with_next_task
            return True

        return False

    def get_next_task(self):
        prev_host_states = self.ansible_iterator._host_states.copy()
        real_task_ind = 1
        result = []

        for host in self.hosts_left:
            while True:
                task = self.ansible_iterator.get_next_task_for_host(host)
                if task[real_task_ind]:
                    if task[real_task_ind].name:
                        result.append(task[real_task_ind])
                        break
                else:
                    break

            # moving iterator to start state
            try:
                prev_host_state = prev_host_states[host.name]
            except KeyError:
                prev_host_state = self.ansible_iterator.get_host_state(host)
            self.ansible_iterator._host_states[host.name] = prev_host_state

        return result

    def skip_next_task(self):
        for host in self.hosts_left:
            self.ansible_iterator.get_next_task_for_host(host)
