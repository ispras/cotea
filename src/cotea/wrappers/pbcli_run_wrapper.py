from cotea.wrappers.wrapper_base import wrapper_base
from cotea.wrappers.ansi_breakpoint import ansi_breakpoint


# wraps from ansible.cli.playbook.PlaybookCLI.run()
class pbcli_run_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger, before_bp_label, after_bp_label):
        super().__init__(func, sync_obj, logger)

        #self.parse_error = False
        self.before_playbook_bp = ansi_breakpoint(sync_obj, before_bp_label)
        self.after_playbook_bp = ansi_breakpoint(sync_obj, after_bp_label)


    # call of PlaybookCLI.run()
    def __call__(self, real_obj):
        self.logger.debug("before playbook")
        self.before_playbook_bp.stop()

        result = self.func(real_obj)

        self.logger.debug("after playbook")
        self.after_playbook_bp.stop()

        return result
