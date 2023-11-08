from cotea.runner import runner
from cotea.arguments_maker import argument_maker
from cotea.debug_utils import interactive_discotech


pb_path = "contr_pb.yaml"
inv = "contr_inv"

arg_maker = argument_maker()

arg_maker.add_arg("-i", inv)

r = runner(pb_path, arg_maker)

while r.has_next_play():
    while r.has_next_task():
        task_results = r.run_next_task()

        some_task_failed = False
        failed_task = None
        for task in task_results:
            if task.is_failed or task.is_unreachable:
                some_task_failed = True
                failed_task = task.task_ansible_object
                break

        if some_task_failed:
            interactive_discotech(failed_task, r)

        r.ignore_errors_of_next_task()

r.finish_ansible()

if r.was_error():
    print("Ansible - failed:")
    print(r.get_error_msg())
else:
    print("Ansible - OK")
