from cotea.wrappers.wrapper_base import wrapper_base


# wraps from ansible.cli.CLI._play_prereqs()
class play_prereqs_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)

        self.loader = None
        self.inventory = None
        self.variable_manager = None

    def __call__(self, real_obj):
        loader, inventory, variable_manager = self.func()
        self.logger.debug("_play_prereqs() call")

        self.loader = loader
        self.inventory = inventory
        self.variable_manager = variable_manager

        return loader, inventory, variable_manager
