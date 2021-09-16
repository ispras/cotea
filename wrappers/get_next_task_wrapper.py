from ansirate.wrappers.wrapper_base import wrapper_base


# wraps ansible.plugins.strategy.linear.StrategyModule._get_next_task_lockstep()
class get_next_task_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)

        self.ansible_iterator = None
        self.hosts_left = None
        self.has_next_task = False

    def __call__(self, real_obj, hosts_left, iterator):
        self.logger.debug("WRAPPER: BEFORE GET_NEXT_TASK")
        real_obj._set_hosts_cache(iterator._play)
        self.hosts_left = hosts_left  # real_obj.get_hosts_left(iterator)
        prev_host_states = iterator._host_states.copy()
        real_task_ind = 1
        tasks_count = 0
        meta_tasks_count = 0
        self.has_next_task = False

        for host in self.hosts_left:
            task = iterator.get_next_task_for_host(host)
            if task[real_task_ind]:
                if task[real_task_ind].get_name() != "meta":
                    tasks_count += 1
                else:
                    meta_tasks_count += 1

            # moving iterator to the starting state
            try:
                prev_host_state = prev_host_states[host.name]
            except KeyError:
                prev_host_state = iterator.get_host_state(host)
            iterator._host_states[host.name] = prev_host_state

        self.ansible_iterator = iterator

        if tasks_count == 0 and meta_tasks_count == 0:
            self.logger.debug("there is no task at all")
            # there is no tasks at all
            self.sync_obj.continue_runner_with_stop()

            result = self.func(real_obj, hosts_left, iterator)
            return result
        else:
            if tasks_count > 0:
                self.logger.debug("there is NORMAL task")
                # no-meta task will be the next one
                self.has_next_task = True

                # flashing control to runner
                self.sync_obj.continue_runner_with_stop()

                result = self.func(real_obj, hosts_left, iterator)
                return result
            else:
                self.logger.debug("there is only META")
                # meta task will be the next one
                result = self.func(real_obj, hosts_left, iterator)
                return result

        # все следующие - meta -> прокручиваем их без стопа и без
        #                         возврата управления
        # следующий - норм таск -> возвращаем управление, говоря true
        # следующих не осталось -> возвращаем управление, говоря false
