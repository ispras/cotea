from ansirate.wrappers.wrapper_base import wrapper_base


# wraps ansible.executor.task_queue_manager.TaskQueueManager.run()
class tqm_run_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)

        self.failed_tasks_hosts = False
        self.failed_hosts_count = None
        self.was_called = False
        self.play_name = ""

    def __call__(self, real_obj, play):
        self.logger.debug("WRAPPER: BEFORE TQM RUN")
        previously_failed = len(real_obj._failed_hosts)
        previously_unreachable = len(real_obj._unreachable_hosts)

        self.was_called = True
        try:
            self.play_name = str(play.get_name())
        except Exception:
            pass

        # call of TaskQueueManager.run()
        result = self.func(real_obj, play)
        self.logger.debug("AFTER TQM, PARAPAPAAAAAAAAAAAAAAAAAAAAAAAAAAM")

        if result & real_obj.RUN_FAILED_BREAK_PLAY != 0:
            self.failed_tasks_hosts = True

        failed_count = len(real_obj._failed_hosts)
        unreachable_count = len(real_obj._unreachable_hosts)
        self.failed_hosts_count = failed_count + unreachable_count - \
                                 (previously_failed + previously_unreachable)

        '''
        self.logger.debug("break_play =", self.failed_tasks_hosts)
        self.logger.debug("failed_hosts_count =", self.failed_hosts_count)
        '''

        self.sync_obj.continue_runner_with_stop()
        self.was_called = False

        return result
