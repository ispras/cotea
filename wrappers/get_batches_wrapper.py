from ansirate.wrappers.wrapper_base import wrapper_base


# wraps ansible.executor.playbook_executor.PlaybookExecutor._get_serialized_batches()
class get_batches_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)
        self.empty_play = False
        self.batches_count = None

    def __call__(self, real_obj, play):
        self.logger.debug("WRAPPER: BEFORE GET_SERIALIZED_BATCHES")
        self.empty_play = False

        # call of PlaybookExecutor._get_serialized_batches()
        res_batches = self.func(real_obj, play)

        if len(res_batches) == 0:
            self.empty_play = True

        if not self.empty_play:
            self.batches_count = len(res_batches[0])

        self.logger.debug("empty play: %s", self.empty_play)
        self.sync_obj.continue_runner_with_stop()

        return res_batches
