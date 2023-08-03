from cotea.wrappers.wrapper_base import wrapper_base
from cotea.wrappers.ansi_breakpoint import ansi_breakpoint


# wraps ansible.plugins.strategy.linear.StrategyModule.run()
class strategy_run_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger, before_bp_label, after_bp_label):
        super().__init__(func, sync_obj, logger)

        self.before_play_bp = ansi_breakpoint(sync_obj, before_bp_label)
        self.after_play_bp = ansi_breakpoint(sync_obj, after_bp_label)
        self.current_play_name = None
        self.iterator = None
        self.play_context = None
        self.variable_manager = None
        self.hosts = None
        self.hosts_all = None
        self.was_error = False
        self.strategy_obj = None
        self.stats = None


    def __call__(self, real_obj, iterator, play_context):
        self.logger.debug("play run")

        self.was_error = False
        self.iterator = iterator
        self.play_context = play_context
        self.variable_manager = real_obj._variable_manager
        self.hosts = real_obj._hosts_cache
        self.hosts_all = real_obj._hosts_cache_all
        self.custom_stats = None
        
        if hasattr(real_obj._tqm, "_stats"):
            if hasattr(real_obj._tqm._stats, "custom"):
                self.custom_stats = real_obj._tqm._stats.custom

        self.strategy_obj = real_obj
        try:
            self.current_play_name = iterator._play.get_name()
        except:
            pass
        
        self.before_play_bp.stop()

        result = self.func(real_obj, iterator, play_context)

        # self.iterator = None
        # self.play_context = None
        # self.current_play_name = None
        
        self.logger.debug("play end")
        
        self.after_play_bp.stop()
        if result != real_obj._tqm.RUN_OK:
            self.was_error = True

        return result
    
