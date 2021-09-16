from ansirate.wrappers.wrapper_base import wrapper_base


# wraps ansible.inventory.manager.InventoryManager.restrict_to_hosts()
class get_batch_len_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger):
        super().__init__(func, sync_obj, logger)
        self.batch_len = None

    def __call__(self, real_obj, batch):
        self.logger.debug("WRAPPER: BEFORE restrict_to_hosts")

        # call of InventoryManager.restrict_to_hosts()
        self.func(real_obj, batch)

        self.batch_len = len(batch)
