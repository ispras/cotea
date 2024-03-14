import json
import os
import threading

import cotea.utils as cotea_utils

# during the imports ansible global objects are created
# that affects to the further work
cotea_utils.remove_modules_from_imported(module_name_like="ansible", not_to_delete="ansible_runner")
cotea_utils.remove_modules_from_imported(module_name_like="logging")

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
    def __init__(self, pb_path, arg_maker, debug_mod=None, show_progress_bar=False,
                 ansible_pb_bin="/usr/local/bin/ansible-playbook"):
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

        if os.path.isfile(ansible_pb_bin):
            self.ansible_pb_bin = ansible_pb_bin
        else:
            raise Exception(f"Ansible playbook bin {ansible_pb_bin} not found")

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

        if self.show_progress_bar:
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
        PlayIterator.add_tasks = self.iterator_add_task_wrp.func
        if self.show_progress_bar:
            PlaybookExecutor.__init__ = self.playbook_executor_wrp.func

    def _except_hook(self, args, /):
        if (args.exc_type == SystemExit or
                # NOTE: this probably should never happen
                args.thread != self.ansible_thread):
            return self._old_except_hook(args)

        self.sync_obj.exception = args.exc_value
        self.sync_obj.continue_runner()

    def _start_ansible(self):
        args = self.arg_maker.args
        args.insert(0, self.ansible_pb_bin)
        args.insert(1, self.pb_path)

        self.pbCLI = PlaybookCLI(args)

        self.ansible_thread = threading.Thread(target=self.pbCLI.run)
        self._old_except_hook = threading.excepthook
        threading.excepthook = self._except_hook

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

        self.task_wrp.set_next_to_prev()

        return res


    def rerun_last_task(self):
        self.task_wrp.rerun_last_task = True


    # returns True and empty string if success
    #         False and error msg otherwise
    def add_new_task(self, new_task_str, is_dict=False):
        prev_task = self.get_prev_task()
        curr_block = None

        has_attrs, error_msg = cotea_utils.obj_has_attrs(prev_task, ["_parent"])
        if not has_attrs:
            return False, error_msg

        curr_block = prev_task._parent
        block_attrs = ["_loader", "_play", "_role", "_variable_manager", "_use_handlers"]
        has_attrs, error_msg = cotea_utils.obj_has_attrs(curr_block, block_attrs)
        if not has_attrs:
            return False, error_msg

        loader = curr_block._loader

        ds = None
        if not is_dict:
            try:
                ds = loader.load(new_task_str)
            except Exception as e:
                error_msg = "Exception during loader.load call, is_dict is {} "
                error_msg += "(from str to python ds): {}"
                return False, error_msg.format(is_dict, str(e))
        else:
            try:
                new_task_str_dict = json.loads(new_task_str)
            except Exception as e:
                error_msg = "Exception during json.loads call, is_dict is {} "
                error_msg += "(from str-aka-dict to python ds): {}"
                return False, error_msg.format(is_dict, str(e))
            ds = [new_task_str_dict]

        #print("DS:\n", ds)

        has_attrs, _ = cotea_utils.obj_has_attrs(ds, ["__len__"])
        if not has_attrs:
            error_msg = "Python repr of the input string should have "
            error_msg += "__len__ attr. Maybe something wrong with input: {}\n"
            error_msg += "Python repr without __len__ attr: {}"
            return False, error_msg.format(new_task_str, str(ds))

        if len(ds) != 1:
            error_msg = "You must add 1 new task. Instead you add: {}"
            return False, error_msg.format(str(ds))

        curr_play = curr_block._play
        #curr_role = curr_block._role
        variable_manager = curr_block._variable_manager
        use_handlers=curr_block._use_handlers

        try:
            new_ansible_task = load_list_of_tasks(
                ds=ds,
                play=curr_play,
                block=curr_block,
                #role=curr_role,
                variable_manager=variable_manager,
                loader=loader,
                use_handlers=use_handlers,
            )

        except Exception as e:
            error_msg = "Exception during load_list_of_tasks call "
            error_msg += "(creats Ansible.Task objects): {}"
            return False, error_msg.format(str(e))

        has_attrs, _ = cotea_utils.obj_has_attrs(new_ansible_task, ["__len__"])
        if not has_attrs:
            error_msg = "Python repr of the input string should have "
            error_msg += "__len__ attr. Maybe something wrong with input: {}\n"
            error_msg += "Python repr without __len__ attr: {}"
            return False, error_msg.format(new_task_str, str(ds))

        new_tasks_count = len(new_ansible_task)
        if new_tasks_count != 1:
            error_msg = "The input '{}' has been interpreted into {} tasks "
            error_msg += "instead of 1. Interpretation result: {}"
            return False, error_msg.format(new_task_str, new_tasks_count, str(ds))

        #self.task_wrp.new_task_to_add = True
        self.task_wrp.new_task = new_ansible_task[0]

        adding_res, error_msg = self.task_wrp.add_tasks(new_ansible_task)

        return adding_res, error_msg


    def get_new_added_task(self):
        return self.task_wrp.new_task


    def ignore_errors_of_next_task(self):
        self.task_wrp.next_task_ignore_errors = True


    def dont_add_last_task_after_new(self):
        self.task_wrp.dont_add_last_task_after_new()


    def get_already_ignore_failed(self):
        return self.task_wrp.should_ignored_errors_uuids


    def get_already_ignore_unrch(self):
        return self.task_wrp.should_ignored_unrch_uuids


    def finish_ansible(self):
        if self.sync_obj.exception is None:
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


    def get_stats(self):
        return self.play_wrp.custom_stats


    def skip_next_task(self):
        skipped_task_name = self.task_wrp.skip_next_task()
        return skipped_task_name