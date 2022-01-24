import threading
import logging
import sys

from ansible.cli import CLI
from ansible.cli.playbook import PlaybookCLI
from ansible.playbook import Playbook, Play
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible import context
from ansible.plugins.strategy import StrategyBase
from ansible.plugins.strategy.linear import StrategyModule
from ansible.executor.task_queue_manager import TaskQueueManager

from cotea.src.ansible_execution_sync import ans_sync
from cotea.src.arguments_maker import argument_maker
from cotea.src.wrappers.get_batches_wrapper import get_batches_wrapper
from cotea.src.wrappers.strategy_run_wrapper import strategy_run_wrapper
from cotea.src.wrappers.get_next_task_wrapper import get_next_task_wrapper
from cotea.src.wrappers.wait_pending_wrapper import wait_pending_wrapper
from cotea.src.wrappers.tqm_run_wrapper import tqm_run_wrapper
from cotea.src.wrappers.get_batch_len_wrapper import get_batch_len_wrapper
from cotea.src.wrappers.pbcli_run_wrapper import pbcli_run_wrapper
from cotea.src.wrappers.play_prereqs_wrapper import play_prereqs_wrapper


class runner:
    def __init__(self, pb_path, arg_maker=None, debug_lvl=None, log_f=None):
        # logger configuration
        if not debug_lvl:
            self.logging_lvl = logging.WARNING  # %(levelname)s:
        else:
            if debug_lvl == "DEBUG":
                self.logging_lvl = logging.DEBUG
            elif debug_lvl == "INFO":
                self.logging_lvl = logging.INFO
            else:
                self.logging_lvl = logging.WARNING

        if log_f is not None:
            logging.basicConfig(format="%(name)s %(asctime)s %(message)s",
                                datefmt="%H:%M:%S", level=self.logging_lvl,
                                filename=log_f, filemode="a")
            self.log_file = open(log_f, "a")
            self.log_file.truncate(0)  # clear file
            sys.stdout = self.log_file
            sys.stderr = self.log_file
        else:
            logging.basicConfig(format="%(name)s %(asctime)s %(message)s",
                                datefmt="%H:%M:%S", level=self.logging_lvl)

        self.logger = logging.getLogger("runner")
        self.logger.debug("runner - INITED")
        self.pb_path = pb_path
        self.arg_maker = arg_maker
        if not arg_maker:
            self.arg_maker = argument_maker()
        else:
            self.logger.debug("ARGMAKER - OK")

        self.wrapper_set = False
        self.setup_play_called_once = False
        self.ansible_thread_run = False
        self.there_was_an_error = False
        self.play_not_loaded = -1
        self.play_ind_in_cur_pb = self.play_not_loaded
        self.sync_obj = ans_sync(logging.getLogger("sync_obj"))

        self._check_pb_and_inv_path()
        self.cur_plays_len = len(self.playbook.get_plays())

        self._set_wrappers()

        args = self.arg_maker.args
        args.insert(0, "/usr/local/bin/ansible-playbook")
        args.insert(1, self.pb_path)

        # getting run string(the same as the cli command)
        self.run_str = ""
        for run_elem in args:
            self.run_str += run_elem + " "

        self.pbCLI = PlaybookCLI(args)

    def _check_pb_and_inv_path(self):
        inv_hosts = ("", )
        loader = DataLoader()
        loader.set_basedir(".")

        passwords = {}

        inventory = InventoryManager(loader, sources=inv_hosts)
        variable_manager = VariableManager(loader=loader,
                                           inventory=inventory)

        # getting playbook
        try:
            pb = Playbook.load(self.pb_path,
                               variable_manager=variable_manager,
                               loader=loader)
        except Exception as e:
            error_msg = "There is something wrong with playbook path or "
            error_msg += "parser has found error in playbook\nError:"
            self.logger.error(error_msg)
            self.logger.error(self.pb_path)
            raise e

        self.playbook = pb  # maybe this will be usable in future

    def _set_wrappers(self):
        wrp_logger = logging.getLogger("ansible_wrappers")

        # setting wrapper on
        # ansible.plugins.strategy.linear.StrategyModule.run()
        # this method is called to run play
        self._run_play_wrp = strategy_run_wrapper(StrategyModule.run,
                                                  self.sync_obj, wrp_logger)
        StrategyModule.run = self._run_play_wrp

        # setting wrapper on
        # ansible.plugins.strategy.linear.StrategyModule._get_next_task_lockstep()
        self._get_next_task_wrp = get_next_task_wrapper(StrategyModule._get_next_task_lockstep,
                                                        self.sync_obj, wrp_logger)
        StrategyModule._get_next_task_lockstep = self._get_next_task_wrp

        # setting wrapper on ansible.plugins.strategy.StrategyBase._wait_on_pending_results()
        # this method is called while waiting for the task ending
        # in most cases this method wait for the same task on different hosts
        self._wait_res_wrp = wait_pending_wrapper(StrategyBase._wait_on_pending_results,
                                                  self.sync_obj, wrp_logger)
        StrategyBase._wait_on_pending_results = self._wait_res_wrp

        # setting wrapper on ansible.executor.playbook_executor._get_serialized_batches()
        self._get_batches_wrp = get_batches_wrapper(PlaybookExecutor._get_serialized_batches,
                                                    self.sync_obj, wrp_logger)
        PlaybookExecutor._get_serialized_batches = self._get_batches_wrp

        # setting wrapper on ansible.executor.task_queue_manager.run()
        self._tqm_run_wrp = tqm_run_wrapper(TaskQueueManager.run,
                                            self.sync_obj, wrp_logger)
        TaskQueueManager.run = self._tqm_run_wrp

        # setting wrapper on ansible.inventory.manager.InventoryManager.restrict_to_hosts()
        self._get_batches_len_wrp = get_batch_len_wrapper(InventoryManager.restrict_to_hosts,
                                                          self.sync_obj, wrp_logger)
        InventoryManager.restrict_to_hosts = self._get_batches_len_wrp

        # setting wrapper on ansible.cli.CLI._play_prereqs()
        self._play_prereqs_wrp = play_prereqs_wrapper(CLI._play_prereqs,
                                                      self.sync_obj, wrp_logger)
        CLI._play_prereqs = self._play_prereqs_wrp

        # setting wrapper on ansible.cli.playbook.PlaybookCLI.run()
        '''
        self._pbcli_run_wrp = pbcli_run_wrapper(PlaybookCLI.run,
                                                self.sync_obj, wrp_logger)
        PlaybookCLI.run = self._pbcli_run_wrp
        '''

    def finish_ansible(self):
        self.logger.debug("we are finishing")

        was_error = self.was_error()

        if was_error or not self._tqm_run_wrp.was_called:
            if was_error:
                self.logger.debug("finishing with errors")
            else:
                self.logger.debug("finishing without errors")
            self.sync_obj.continue_ansible()
        else:
            self.logger.debug("finishing without errors")
            self.sync_obj.continue_ansible_with_stop()
            self.sync_obj.continue_ansible()

    def has_next_play(self):
        self.logger.debug("HAS_NEXT_PLAY CALL")
        # Ansible will stop his work anyway if there was failed task
        # and there was no 'ignore_errors'

        result = True

        if self.there_was_an_error:
            self.logger.debug("THERE WAS FAILED TASK")
            result = False

        # so strange because self.play_ind_in_cur_pb initial value is -1
        if self.play_ind_in_cur_pb + 1 > self.cur_plays_len - 1:
            result = False
        self.logger.debug("HAS_NEXT_PLAY from python: result = %s" % result)
        self.logger.debug("HAS_NEXT_PLAY from python: cur_play_ind = %d",
                          self.play_ind_in_cur_pb + 1)
        self.logger.debug("HAS_NEXT_PLAY from python: cur_play_ind = %d",
                          self.cur_plays_len - 1)

        return result

    def setup_play_for_run(self):
        self.logger.debug("SETUP_PLAY_FOR_RUN CALL")

        self.play_ind_in_cur_pb += 1
        if self.play_ind_in_cur_pb > self.cur_plays_len - 1:
            return False

        if not self.ansible_thread_run:
            try:
                self.ansible_thread_run = True
                ansible_thread = threading.Thread(target=self.pbCLI.run)
                ansible_thread.start()
            except Exception as e:
                self.logger.error("Ansible launch was failed\n")
                self.logger.error("Error:")
                raise e

        if self.play_ind_in_cur_pb == 0:  # first play in pb
            self.sync_obj.runner_just_wait()
        else:
            self.sync_obj.continue_ansible_with_stop()

        # this is not first play
        if self.setup_play_called_once and self._tqm_run_wrp.was_called:
            # there was an error
            if self.was_error():
                self.there_was_an_error = True
                return False

            self.sync_obj.continue_ansible_with_stop()

        if self._get_batches_wrp.empty_play:
            return False

        self.sync_obj.continue_ansible_with_stop()

        self._wait_res_wrp.ansible_iterator = self._run_play_wrp.ansible_iterator
        self._wait_res_wrp.hosts_left = self._run_play_wrp.hosts_left

        self.setup_play_called_once = True

        return True

    def has_next_task(self):
        self.logger.debug("HAS_NEXT_TASK CALL")

        self.sync_obj.continue_ansible_with_stop()

        '''
        if self.some_task_was_failed:
            self.logger.debug("THERE WAS FAILED TASK")
            return False
        '''

        res = self._get_next_task_wrp.has_next_task
        self.logger.debug("HAS_NEXT_TASK RES = %s", res)
        return res

    def run_next_task(self):
        self.logger.debug("RUN_NEXT_TASK CALL")
        self.sync_obj.continue_ansible_with_stop()
        if self._wait_res_wrp.failed_task:
            self.some_task_was_failed = True
            return False

        return True

    # returns tasks of current play as a dict, where each host
    # is a key and its value is list of its tasks
    def get_cur_play_tasks(self):
        self.logger.info(self._run_play_wrp.cur_play_hosts_tasks)
        return self._run_play_wrp.cur_play_hosts_tasks

    # returns all gotten task results
    # each result is an object of ansible.executor.task_result class
    def get_results(self):
        return self._wait_res_wrp.results

    # returns results of last pass(last run task on each host)
    def get_last_results(self):
        res = self._wait_res_wrp.results
        return res[len(res) - 1]

    def make_results_pretty_print(self):
        self._wait_res_wrp.print_results()

    # returns list of next tasks for each host of the play
    def get_next_task_name(self):
        next_tasks = self._wait_res_wrp.get_next_task()
        result_name = ""

        try:
            result_name = str(next_tasks[0].name)
        except Exception:
            pass
        # self.logger.info(next_task)
        return result_name

    def get_cur_play_name(self):
        return self._tqm_run_wrp.play_name

    # will skip next task on every host
    def skip_next_task(self):
        self._wait_res_wrp.skip_next_task()

    def get_all_vars(self):
        all_vars = self._play_prereqs_wrp.variable_manager.get_vars()
        return all_vars

    def get_all_facts(self):
        facts = self._play_prereqs_wrp.variable_manager._fact_cache.copy()
        return facts

    def get_variable(self, var_name):
        if var_name == "ansible_facts":
            facts = self.get_all_facts()
            return facts

        all_vars = self._play_prereqs_wrp.variable_manager.get_vars()

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

        self.logger.info("There is no variable with name " + str(var_name))
        return None

    def was_error(self):
        if self._tqm_run_wrp.failed_tasks_hosts:
            return True

        if self._get_batches_wrp.batches_count:
            compare_with = self._get_batches_wrp.batches_count
        if self._get_batches_len_wrp.batch_len:
            compare_with = self._get_batches_len_wrp.batch_len

        self.logger.debug("From restrict: %d",
                          self._get_batches_len_wrp.batch_len)
        self.logger.debug("From batches: %d",
                          self._get_batches_wrp.batches_count)

        if self._tqm_run_wrp.failed_hosts_count == compare_with:
            return True

        return False

    def get_error_msg(self):
        # this is object of ansible.executor.TaskResult class
        last_task_result = self.get_last_results()

        msg = ""

        if len(last_task_result) > 0:
            if last_task_result[0]._result:
                if "msg" in last_task_result[0]._result:
                    try:
                        msg = str(last_task_result[0]._result["msg"])
                    except Exception as e:
                        self.logger.debug(e)
                        msg = ""

        self.logger.debug("get_error_msg res = %s", msg)
        self.logger.debug(type(msg))
        return msg

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
            self.logger.debug("During runner._getIP() call error was occured. We skipped it.")
            self.logger.debug("Error is:\n%s", e)

        self.logger.debug("get_ip res = %s", res)
        self.logger.debug(type(res))
        return res

    def get_run_string(self):
        self.logger.debug("get_run_string res = %s", self.run_str)
        return str(self.run_str)
