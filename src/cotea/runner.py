import logging
import threading

from ansible.cli import CLI
from ansible.plugins.strategy.linear import StrategyModule
from ansible.plugins.strategy import StrategyBase
from ansible.cli.playbook import PlaybookCLI
from ansible.parsing.yaml.objects import AnsibleUnicode

from cotea.ansible_execution_sync import ans_sync
from cotea.task_result import TaskResult
from cotea.wrappers.pbcli_run_wrapper import pbcli_run_wrapper
from cotea.wrappers.strategy_run_wrapper import strategy_run_wrapper
from cotea.wrappers.get_next_task_wrapper import get_next_task_wrapper
from cotea.wrappers.update_active_conn_wrapper import update_active_conn_wrapper
from cotea.wrappers.play_prereqs_wrapper import play_prereqs_wrapper


class runner:
    def __init__(self, pb_path, arg_maker, debug_mod=None):
        logging_lvl = logging.INFO
        if debug_mod:
            logging_lvl= logging.DEBUG
        
        logging.basicConfig(format="%(name)s %(asctime)s %(message)s", \
                    datefmt="%H:%M:%S", level=logging_lvl)

        self.pb_path = pb_path
        self.arg_maker = arg_maker

        self.logger = logging.getLogger("RUNNER")
        
        log_sync = logging.getLogger("SYNC")
        self.sync_obj = ans_sync(log_sync)

        self.breakpoint_labeles = {}
        self.breakpoint_labeles["before_playbook"] = "before_playbook_run"
        self.breakpoint_labeles["after_playbook"] = "after_playbook_run"
        self.breakpoint_labeles["before_play"] = "before_play_run"
        self.breakpoint_labeles["after_play"] = "after_play_run"
        self.breakpoint_labeles["before_task"] = "before_task_run"
        self.breakpoint_labeles["after_task"] = "after_task_run"

        self._set_wrappers()
        start_ok = self._start_ansible()
        self.logger.debug("Ansible start ok: %s", start_ok)
        

    def _set_wrappers(self):
        wrp_lgr = logging.getLogger("WRPR")

        self.pbcli_run_wrp = pbcli_run_wrapper(PlaybookCLI.run, self.sync_obj, wrp_lgr,
                                               self.breakpoint_labeles["before_playbook"],
                                               self.breakpoint_labeles["after_playbook"])
        PlaybookCLI.run = self.pbcli_run_wrp

        self.play_wrp = strategy_run_wrapper(StrategyModule.run, self.sync_obj, wrp_lgr,
                                             self.breakpoint_labeles["before_play"],
                                             self.breakpoint_labeles["after_play"])
        StrategyModule.run = self.play_wrp

        self.task_wrp = get_next_task_wrapper(StrategyModule._get_next_task_lockstep,
                                              self.sync_obj, wrp_lgr,
                                              self.breakpoint_labeles["before_task"])
        StrategyModule._get_next_task_lockstep = self.task_wrp

        self.update_conn_wrapper = update_active_conn_wrapper(StrategyBase.update_active_connections,
                                                              self.sync_obj, wrp_lgr,
                                                              self.breakpoint_labeles["after_task"])
        StrategyBase.update_active_connections = self.update_conn_wrapper

        self.play_prereqs_wrp = play_prereqs_wrapper(CLI._play_prereqs,
                                                      self.sync_obj, wrp_lgr)
        CLI._play_prereqs = self.play_prereqs_wrp
    

    def _start_ansible(self):
        args = self.arg_maker.args
        args.insert(0, "/usr/local/bin/ansible-playbook")
        args.insert(1, self.pb_path)

        self.pbCLI = PlaybookCLI(args)

        self.ansible_thread = threading.Thread(target=self.pbCLI.run)
        self.ansible_thread.start()
        self.sync_obj.runner_just_wait()

        if self.sync_obj.curr_breakpoint_label == self.breakpoint_labeles["before_playbook"]:
            return True
        
        return False
    

    def has_next_play(self):
        if self.sync_obj.curr_breakpoint_label == self.breakpoint_labeles["after_playbook"]:
            return False
        
        self.sync_obj.continue_ansible_with_stop()
        current_bp_label = self.sync_obj.curr_breakpoint_label
        self.logger.debug("has_next_play: %s", current_bp_label)

        if current_bp_label == self.breakpoint_labeles["before_play"]:
            return True

        return False


    def has_next_task(self):
        if self.sync_obj.curr_breakpoint_label == self.breakpoint_labeles["after_playbook"]:
            return False

        self.sync_obj.continue_ansible_with_stop()
        current_bp_label = self.sync_obj.curr_breakpoint_label
        self.logger.debug("has_next_task: %s", current_bp_label)

        if current_bp_label == self.breakpoint_labeles["before_task"]:
            return True

        return False


    def run_next_task(self):
        res = []

        if self.sync_obj.curr_breakpoint_label == self.breakpoint_labeles["after_playbook"]:
            return res

        self.sync_obj.continue_ansible_with_stop()
        current_bp_label = self.sync_obj.curr_breakpoint_label
        self.logger.debug("run_next_task: %s", current_bp_label)

        if current_bp_label != self.breakpoint_labeles["after_task"]:
            self.logger.debug("run_next_task() has come not in to the 'after_task'")
        
        for task_result_ansible_obj in self.update_conn_wrapper.current_results:
            res.append(TaskResult(task_result_ansible_obj))
        
        return res
    

    def schedule_last_task_again(self):
        self.task_wrp.run_last_one = True


    def finish_ansible(self):
        while self.sync_obj.curr_breakpoint_label != self.breakpoint_labeles["after_playbook"]:
            self.sync_obj.continue_ansible_with_stop()
        
        self.sync_obj.continue_ansible()
    

    def get_cur_play_name(self):
        return str(self.play_wrp.current_play_name)
    

    def get_next_task(self):
        return self.task_wrp.get_next_task()


    def get_next_task_name(self):
        return str(self.task_wrp.get_next_task_name())
    

    def get_prev_task(self):
        return self.task_wrp.get_prev_task()
    

    def get_prev_task_name(self):
        return str(self.task_wrp.get_prev_task_name())
    

    def get_last_task_result(self):
        res = []

        for task_result_ansible_obj in self.update_conn_wrapper.current_results:
            res.append(TaskResult(task_result_ansible_obj))

        return res
    

    # returns True if there was an non ignored error
    def was_error(self):
        return self.play_wrp.was_error
    

    # returns list with all errors, including the ignored ones
    def get_all_error_msgs(self):
        return self.update_conn_wrapper.error_msgs
    

    # returns last error msg that wasn't ignored 
    def get_error_msg(self):
        res = ""

        # the errors didn't have 'ignore_errors'
        if self.was_error():
            errors_count = len(self.update_conn_wrapper.error_msgs)

            if errors_count > 0:
                res = self.update_conn_wrapper.error_msgs[errors_count - 1]
        
        return res
    

    def get_all_vars(self):
        variable_manager = self.play_wrp.variable_manager
        cur_play = self.play_wrp.iterator._play
        hosts = self.play_wrp.hosts
        hosts_all = self.play_wrp.hosts_all

        res = variable_manager.get_vars(play=cur_play,
                                        _hosts=hosts,
                                        _hosts_all=hosts_all)

        return res


    def get_all_facts(self):
        return self.play_prereqs_wrp.variable_manager._fact_cache.copy()


    def get_variable(self, var_name):
        if var_name == "ansible_facts":
            return self.get_all_facts()

        all_vars = self.get_all_vars()

        if var_name in all_vars:
            return all_vars[var_name]

        # check groups
        if "groups" in all_vars:
            if var_name in all_vars["groups"]:
                return all_vars["groups"][var_name]

        result = {}

        # check hostvars
        if "hostvars" in all_vars:
            for host in all_vars["hostvars"]:
                for key in all_vars["hostvars"][host]:
                    if key == var_name:
                        result[host] = {key: all_vars["hostvars"][host][key]}

        if result:
            return result

        facts = self.get_all_facts()
        for host_key in facts:
            if var_name in facts[host_key]:
                result[host_key] = facts[host_key][var_name]

        if result:
            return result

        self.logger.info("There is no variable with name %s", var_name)

        return None
    

    def add_var_as_extra_var(self, new_var_name, value):
        variable_manager = self.play_wrp.variable_manager

        ansible_way_var = AnsibleUnicode(new_var_name)
        variable_manager._extra_vars[ansible_way_var] = value
   
    
    def _getIP(self):
        var_name = "openstack_servers"
        host_name = "localhost"
        ip1_field_name = "interface_ip"
        ip2_field_name = "private_v4"

        res = ""
        ostack_var = self.get_variable(var_name)

        try:
            if ip1_field_name in ostack_var[host_name][0]:
                res = str(ostack_var[host_name][0][ip1_field_name])
            elif ip2_field_name in ostack_var[host_name][0]:
                res = str(ostack_var[host_name][0][ip2_field_name])
        except Exception as e:
            self.logger.info("During runner._getIP() call error was occured. We skipped it.")
            self.logger.info("Error is:\n%s", e)

        self.logger.debug("get_ip res = %s", res)
        self.logger.debug(type(res))

        return res

