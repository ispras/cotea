from ansirate.wrappers.wrapper_base import wrapper_base


# wraps from ansible.cli.playbook.PlaybookCLI.run()
class pbcli_run_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)

        self.parse_error = False

    def __call__(self, real_obj):
        # call of PlaybookCLI.run()
        result = self.func(real_obj)

        '''
        self.logger.debug("After pb_cli_run")
        self.logger.debug("Result = %s", result)
        '''
        return result
