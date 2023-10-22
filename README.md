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
pip install cotea
```

## Quick start
```python
from cotea.runner import runner
from cotea.arguments_maker import argument_maker

inv_path = "/path/to/inventory"
playbook_path = "/path/to/playbook"

arg_maker = argument_maker()

# setting ansible-playbook flags
arg_maker.add_arg("-i", inv_path)
arg_maker.add_arg("-vvv")

# setting extra-vars
extra_vars = {"SPARK_VERSION": "3.0.2"}
arg_maker.add_arg("--extra-vars", extra_vars)

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
With the help of cotea one can do certain things dynamically at specific Ansible execution points.

## Debugging 

```python
# imports and object creation...

while r.has_next_play():
    while r.has_next_task():
        task_results = r.run_next_task()
    
        some_task_failed = False
        failed_task = None

        already_ignore_failed = r.get_already_ignore_failed()
        already_ignore_unrch = r.get_already_ignore_unrch()

        for task in task_results:
            task_uuid = task.original_task_uuid
            
            # checking that task didn't have ignore_errors: true
            if task.is_failed:    
                if not task_uuid in already_ignore_failed:
                    some_task_failed = True
                    failed_task = task.task_ansible_object
                    break
            
            # checking that task didn't have ignore_unreachable: true
            if task.is_unreachable:    
                if not task_uuid in already_ignore_unrch:
                    some_task_failed = True
                    failed_task = task.task_ansible_object
                    break
        
        # the task was failed and didn't have
        # ignore_errors or ignore_unreachable flags -
        # going to interactive debugging mod
        if some_task_failed:
            interactive_discotech(failed_task, r)

        r.ignore_errors_of_next_task()


r.finish_ansible()

if r.was_error():
    print("Ansible error was:", r.get_error_msg())
```
Cotea also contains interactive debugging mode. Using the cotea one can detects that the task was failed in runtime (including the check that task didn't have ignore_errors or ignore_unreachable flag) and call the *interactive_discotech()* method in that case as shown above.  Supported commands:
- 'ft' - print info about the Failed Task
- 'msg' - print all ansible error MSGs (including the ignored ones)
- 'p' - print Progress bar
- 'h'/'help' - print help message
- 're' - RErun of the failed task
- 'v' - add new Variable as extra var
- 'c' - Continue ansible execution (go to the next task)
- 'nt' - add New Task
- 'w' - Watch ansible variable value

A detailed overview of all interfaces is provided in [cotea documentation](https://github.com/ispras/cotea/blob/main/docs/cotea_docs.md).