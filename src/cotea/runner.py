import threading

from cotea.utils import remove_modules_from_imported

# during the imports ansible global objects are created
# that affects to the further work
remove_modules_from_imported(module_name_like="ansible", not_to_delete="ansible_runner")
remove_modules_from_imported(module_name_like="logging")

from ansible.cli import CLI
from ansible.plugins.strategy.linear import StrategyModule
from ansible.plugins.strategy import StrategyBase
from ansible.cli.playbook import PlaybookCLI
from ansible.parsing.yaml.objects import AnsibleUnicode
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.play_iterator import PlayIterator
from ansible import constants as C
from ansible.playbook.task import Task
from ansible.playbook.helpers import load_list_of_tasks

from cotea.ansible_execution_sync import ans_sync
from cotea.task_result import TaskResult
from cotea.wrappers.pbcli_run_wrapper import pbcli_run_wrapper
from cotea.wrappers.strategy_run_wrapper import strategy_run_wrapper
from cotea.wrappers.get_next_task_wrapper import get_next_task_wrapper
from cotea.wrappers.update_active_conn_wrapper import update_active_conn_wrapper
from cotea.wrappers.play_prereqs_wrapper import play_prereqs_wrapper
from cotea.wrappers.playbook_executor_wrapper import play_executor_wrapper
from cotea.wrappers.iterator_add_task_wrapper import iterator_add_task_wrapper
from cotea.progress_bar import ansible_progress_bar
from cotea.ansible_execution_tree import AnsibleExecTree

import logging



class runner:
    def __init__(self, pb_path, arg_maker, debug_mod=None, show_progress_bar=False):
        logging_lvl = logging.INFO
        if debug_mod:
            logging_lvl= logging.DEBUG
        
        self.show_progress_bar = show_progress_bar
        
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

        self.progress_bar = ansible_progress_bar()
        self.execution_tree = AnsibleExecTree()

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
                                              self.breakpoint_labeles["before_task"],
                                              self.progress_bar,
                                              self.show_progress_bar)
        StrategyModule._get_next_task_lockstep = self.task_wrp

        self.update_conn_wrapper = update_active_conn_wrapper(StrategyBase.update_active_connections,
                                                              self.sync_obj, wrp_lgr,
                                                              self.breakpoint_labeles["after_task"])
        StrategyBase.update_active_connections = self.update_conn_wrapper

        self.play_prereqs_wrp = play_prereqs_wrapper(CLI._play_prereqs,
                                                      self.sync_obj, wrp_lgr)
        CLI._play_prereqs = self.play_prereqs_wrp

        self.playbook_executor_wrp = play_executor_wrapper(PlaybookExecutor.__init__,
                                                           self.sync_obj, wrp_lgr,
                                                           self.execution_tree,
                                                           self.progress_bar)
        PlaybookExecutor.__init__ = self.playbook_executor_wrp

        self.iterator_add_task_wrp = iterator_add_task_wrapper(PlayIterator.add_tasks,
                                                                  self.sync_obj, wrp_lgr,
                                                                  self.execution_tree,
                                                                  self.progress_bar)
        PlayIterator.add_tasks = self.iterator_add_task_wrp
    

    def _set_wrappers_back(self):
        PlaybookCLI.run = self.pbcli_run_wrp.func
        StrategyModule.run = self.play_wrp.func
        StrategyModule._get_next_task_lockstep = self.task_wrp.func
        StrategyBase.update_active_connections = self.update_conn_wrapper.func
        CLI._play_prereqs = self.play_prereqs_wrp.func
        PlaybookExecutor.__init__ = self.playbook_executor_wrp.func
        PlayIterator.add_tasks = self.iterator_add_task_wrp.func
    

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
    

    def rerun_last_task(self):
        self.task_wrp.rerun_last_task = True
    

    # returns True and empty string if success
    #         False and error msg otherwise
    def add_new_task(self, new_task_str):
        loader = self.playbook_executor_wrp.loader

        ds = None
        try:
            ds = loader.load(new_task_str)
        except Exception as e:
            return False, "Exception during loader.load call\
                (from str to python ds): {}".format(str(e))
        
        if hasattr(ds, "__len__"):
            if len(ds) != 1:
                return False, "You must add 1 new task. Instead you add: {}".format(str(ds))
        else:
            return False, "Python repr of the input string should have\
                        __len__ attr. Maybe something wrong with input: {}\n\
                        Python repr without __len__ attr: {}".format(new_task_str, str(ds))

        current_play = self.play_wrp.iterator._play
        variable_manager = self.playbook_executor_wrp.variable_manager

        try:
            new_ansible_task = load_list_of_tasks(ds=ds, play=current_play, \
                variable_manager=variable_manager, loader=loader)
        except Exception as e:
            return False, "Exception during load_list_of_tasks call\
                (creats Ansible.Task objects): {}".format(str(e))
        
        if hasattr(new_ansible_task, "__len__"):
            new_tasks_count = len(new_ansible_task)
            if new_tasks_count != 1:
                return False, "The input '{}' has been interpreted into {} tasks\
                               instead of 1. Interpretation \
                                result: {}".format(new_task_str, new_tasks_count, str(ds))
        else:
            return False, "Python repr of the input string should have\
                        __len__ attr. Maybe something wrong with input: {}\n\
                        Python repr without __len__ attr: {}".format(new_task_str, str(ds))
        
        # new_task doesn't have parent and parent_type attrs
        # we will take them from previous task
        new_task = new_ansible_task[0]
        ser_new_task = new_task.serialize()
        
        prev_task = self.get_prev_task()
        ser_prev_task = prev_task.serialize()

        if "parent" not in ser_prev_task:
            return False, "Previous task doesn't have 'parent' attr but should.\n\
                Previous task serialize view: {}".format(str(ser_prev_task))

        if hasattr(ser_prev_task["parent"], "copy"):
            ser_new_task["parent"] = ser_prev_task["parent"].copy()
        else:
            return False, "Previous task 'parent' attr doesn't have 'copy' attr but should\
                 because it should be dict. 'parent' attr: {}".format(str(ser_prev_task))

        if "parent_type" not in ser_prev_task:
            return False, "Previous task doesn't have 'parent_type' attr but should.\n\
                Previous task serialize view: {}".format(str(ser_prev_task))
        
        ser_new_task["parent_type"] = ser_prev_task["parent_type"]

        final_new_task = Task()
        final_new_task.deserialize(ser_new_task)

        # needs to be processed properly
        try:
            final_new_task._parent._play = prev_task._parent._play.copy()
        except:
            final_new_task._parent._play = current_play.copy() 
        
        self.task_wrp.new_task_to_add = True
        self.task_wrp.new_task = final_new_task

        return True, ""

    
    def ignore_errors_of_next_task(self):
        self.task_wrp.next_task_ignore_errors = True

    def get_already_ignore_failed(self):
        return self.task_wrp.already_ignore_failed


    def get_already_ignore_unrch(self):
        return self.task_wrp.already_ignore_unrch


    def finish_ansible(self):
        while self.sync_obj.curr_breakpoint_label != self.breakpoint_labeles["after_playbook"]:
            self.sync_obj.continue_ansible_with_stop()
        
        self.sync_obj.continue_ansible()
        self.ansible_thread.join(timeout=5)
        self._set_wrappers_back()
    

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

