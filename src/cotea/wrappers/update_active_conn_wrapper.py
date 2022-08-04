from cotea.wrappers.wrapper_base import wrapper_base
from cotea.wrappers.ansi_breakpoint import ansi_breakpoint


# wraps ansible.plugins.strategy.StrategyBase.update_active_connections()
class update_active_conn_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger, bp_label):
        super().__init__(func, sync_obj, logger)

        self.after_task_bp = ansi_breakpoint(sync_obj, bp_label)
        self.current_results = None
        self.error_msgs = []

    def __call__(self, real_obj, results):
        result = self.func(real_obj, results)
        self.current_results = results
        self._save_error_msgs(results)
        self.after_task_bp.stop()
        
        '''
        self.logger.info("task end, result:")
        if len(results) > 0:
            #self.logger.info(results[0].is_failed())
            #self.logger.info(dir(results[0]))
            if results[0].is_failed():
                self.logger.info(results[0]._result["stderr_lines"])
        #self.sync_obj.continue_runner_with_stop()
        '''

        return result


    def _save_error_msgs(self, results):
        for res in results:
            if res.is_failed() or res.is_unreachable():
                if hasattr(res, "_result"):
                    if "stderr" in res._result:
                        self.error_msgs.append(str(res._result["stderr"]))
                    elif "msg" in res._result:
                        self.error_msgs.append(str(res._result["msg"]))
                    elif "exception" in res._result:
                        self.error_msgs.append(str(res._result["exception"]))
