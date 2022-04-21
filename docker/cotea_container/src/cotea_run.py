from cotea.runner import runner
from cotea.arguments_maker import argument_maker

pb_path = "main.yaml"

arg_maker = argument_maker()
arg_maker.add_arg("-i", "inv")


r = runner(pb_path, arg_maker)

while r.has_next_play():
    while r.has_next_task():
        r.run_next_task()

r.finish_ansible()

if r.was_error():
    print("ansible-playbook launch - ERROR:")
    print(r.get_error_msg())
else:
    print("ansible-playbook launch - OK")
