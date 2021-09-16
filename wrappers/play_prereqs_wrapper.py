from ansirate.wrappers.wrapper_base import wrapper_base


# wraps from ansible.cli.CLI._play_prereqs()
class play_prereqs_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)

        self.loader = None
        self.inventory = None
        self.variable_manager = None

    def __call__(self, real_obj):
        loader, inventory, variable_manager = self.func()
        self.logger.debug("_pre_reqs call")

        if not self.loader:
            self.loader = loader

        if not self.inventory:
            self.inventory = inventory

        if not self.variable_manager:
            self.variable_manager = variable_manager

        return loader, inventory, variable_manager
