from ansible.executor.play_iterator import PlayIterator
from ansible.playbook.task import Task
from ansible.playbook.block import Block

from cotea.wrappers.wrapper_base import wrapper_base
from cotea.progress_bar import ansible_progress_bar
from cotea.ansible_execution_tree import AnsibleExecTree

TASK_IND = 1


# wraps from ansible.executor.play_iterator.PlayIterator.add_tasks()
class iterator_add_task_wrapper(wrapper_base):
    def __init__(self, func, sync_obj, logger, exec_tree: AnsibleExecTree,
                 progress_bar: ansible_progress_bar):
        super().__init__(func, sync_obj, logger)

        self.ansible_exec_tree = exec_tree
        self.progress_bar = progress_bar


    def __call__(self, real_obj: PlayIterator, host, all_blocks):
        res = self.func(real_obj, host, all_blocks)
        
        play_name = real_obj._play.get_name()
        host_name = str(host)

        self.ansible_exec_tree.add_play(play_name)
        for block in all_blocks:
            block_tasks = _get_all_block_tasks(block)
            for task_name in block_tasks:
                self.ansible_exec_tree.add_task(play_name, host_name, task_name)

        self.ansible_exec_tree.compute_metrics()
        self.progress_bar.set_total_task_count(self.ansible_exec_tree.task_count)

        # except Exception as e:
        #     print("--------Bug find print--------")

        #     print("Exception is: ", e)
        #     print("Play name: ", play_name)
        #     print("Blocks: ", all_blocks)

        #     block_num = 1
        #     for block in all_blocks:
        #         print("Block num =", block_num)
        #         for task in block.block:
        #             print("type of blocks.block elem: ", type(task))
        #             print("blocks.block elem:", task, "\n")

        #             if hasattr(task, "block"):
        #                 print(task.block)
                
        #         block_num += 1

        #     print("------------------------------")

        return res


def _get_all_block_tasks(block):
    new_tasks = []

    _get_all_block_tasks_rec(new_tasks, block)

    return new_tasks


def _get_all_block_tasks_rec(new_tasks: list, block: Block):
    if hasattr(block, "block"):
        for task_or_block in block.block:
            if isinstance(task_or_block, Task):
                if hasattr(task_or_block, "get_name"):
                    #print("\tappending")
                    new_tasks.append(task_or_block.get_name())
                else:
                    print("task has no 'get_name' attr:", task_or_block)
            
            elif isinstance(task_or_block, Block):
                _get_all_block_tasks_rec(new_tasks, task_or_block)
            
            else:
                print("in 'block' list object is not Task/Block type:", type(task_or_block), task_or_block)

    #else:
    #    print("block has no 'block' attr:", block)