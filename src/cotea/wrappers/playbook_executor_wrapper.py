import tempfile

from ansible.playbook.play_context import PlayContext
from ansible.executor.play_iterator import PlayIterator
from ansible.playbook import Playbook
from ansible.template import Templar

from cotea.wrappers.wrapper_base import wrapper_base
from cotea.ansible_execution_tree import AnsibleExecTree
from cotea.progress_bar import ansible_progress_bar

TASK_IND = 1


# wraps from ansible.executor.playbook_executor.PlaybookExecutor()
class play_executor_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger, exec_tree: AnsibleExecTree,
                 progress_bar: ansible_progress_bar):
        super().__init__(func, sync_obj, logger)

        self.ansible_exec_tree = exec_tree
        self.progress_bar = progress_bar

        self.loader = None
        self.variable_manager = None
        self.inventory = None


    def __call__(self, real_obj, playbooks, inventory, variable_manager, loader, passwords):
        self.loader = loader
        self.variable_manager = variable_manager
        self.inventory = inventory

        self.func(real_obj, playbooks, inventory, variable_manager, loader, passwords)
        connection_lockfile = tempfile.TemporaryFile()

        for playbook in playbooks:
            pb = Playbook.load(playbook, variable_manager, loader)

            plays = pb.get_plays()

            for play in plays:
                new_play = play.copy()
                play_name = play.get_name()
                play_context = PlayContext(new_play, passwords, connection_lockfile)

                all_vars = variable_manager.get_vars(play=play)
                iterator = PlayIterator(
                    inventory=inventory,
                    play=new_play,
                    play_context=play_context,
                    variable_manager=variable_manager,
                    all_vars=all_vars,
                    start_at_done=False,
                )

                hosts_cache = _get_hosts_cache(new_play, inventory)
                hosts_left = _get_hosts_left(inventory, iterator, hosts_cache)

                self.ansible_exec_tree.add_play(play_name)
                
                for host in hosts_left:
                    host_str = str(host)
                    while True:
                        task = iterator.get_next_task_for_host(host)
                        if not task[TASK_IND]:
                            break
                        
                        if hasattr(task[TASK_IND], "get_name"):
                            task_name = task[TASK_IND].get_name()
                            self.ansible_exec_tree.add_task(play_name, host_str, task_name)
                        else:
                            self.logger.debug("playbook executor, task[TASK_IND] has no attr get_name: ", task[TASK_IND])
        
        self.ansible_exec_tree.compute_metrics()
        self.progress_bar.set_total_task_count(self.ansible_exec_tree.task_count)
        #self.ansible_exec_tree.pretty_print()



def _get_hosts_cache(play, inventory):
    if Templar(None).is_template(play.hosts):
        _pattern = 'all'
    else:
        _pattern = play.hosts or 'all'
    
    hosts_cache_all = [h.name for h in inventory.get_hosts(pattern=_pattern, ignore_restrictions=True)]
    hosts_cache = [h.name for h in inventory.get_hosts(play.hosts, order=play.order)]

    return hosts_cache
    

def _get_hosts_left(inventory, iterator, hosts_cache):
    hosts_left = []
    for host in hosts_cache:
        try:
            hosts_left.append(inventory.hosts[host])
        except KeyError:
            hosts_left.append(inventory.get_host(host))
    return hosts_left