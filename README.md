# cotea

#### (COntrol Thread Execution Ansible)

### cotea is:
Tool that provides Python API to run Ansible programmatically.

### cotea allows:
- **To control** Ansible execution by iterating over the Ansible plays and tasks
- **To embed** Ansible into another system
- **To debug** Ansible execution by getting the values of Ansible variables and by retrieving the results of the execution of Ansible tasks/plays

## Installation
```bash
pip install -i https://test.pypi.org/simple/ cotea==1.3.2
```

Tested on Ansible 2.9.4, 2.12.2, 2.12.4 in ubuntu 20.04.

## Quick start
```python
from cotea.runner import runner
from cotea.arguments_maker import argument_maker

inv_path = "/path/to/inventory"
playbook_path = "/path/to/playbook"

am = argument_maker()
am.add_arg("-i", inv_path)

r = runner(playbook_path, am)

while r.has_next_play():
    current_play = r.get_cur_play_name()
    print("PLAY:", current_play)

    while r.has_next_task():
        next_task = r.get_next_task_name()
        print("\tTASK:", next_task)
            
        r.run_next_task()

r.finish_ansible()
```
Any argument of the "ansible-playbook" command can be passed by using **argument_maker** objects.
The launch and control of the Ansible is carried out using the **runner** object.

## Debugging 

```python
# imports and object creation...

specific_play = "s_play"
specific_task = "s_task"
s_var_name = "s_var"

while r.has_next_play():
    current_play = r.get_cur_play_name()

    while r.has_next_task():
        next_task = r.get_next_task_name()
        if current_play == specific_play and next_task == specific_task:
            # getting variable at specific execution point
            s_var_value = r.get_variable(s_var_name)

        r.run_next_task()

r.finish_ansible()

if r.was_error():
    print("Ansible error was:", r.get_error_msg())
```
With the help of cotea one can do certain things dynamically at specific Ansible execution points. Getting the value of a specific variable at a specific execution point is shown above (the point is determined by a pair of Ansible play and task). If ansible exits with an error one can get the error message programmatically without processing a huge log file.

A detailed overview of all interfaces is provided in [cotea documentation](https://github.com/ispras/cotea/blob/main/docs/cotea_docs.md).
