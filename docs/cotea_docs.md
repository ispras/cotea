# cotea documentation

The [runner](https://github.com/ispras/cotea/blob/main/src/runner.py#L29) class is the main class in *cotea*. It wraps *ansible-playbook* command. With the use of *runner* class, user runs and controls Ansible programmatically, gets additional information about the execution.

The second point of interaction is the [argument_maker](https://github.com/ispras/cotea/blob/main/src/arguments_maker.py#L1) class. With the use of it, user can pass any argument for Ansible launch just like he passed arguments for *ansible-playbook* in the command line.

## argument_maker

The constructor of this class does not accept arguments. The class has only one method:

**add_arg(self, param_name, value=None)**
- *param_name* is the name of argument in the same notation as the *ansible-playbook* command line arguments names. For example, "-i" or "--extra-vars".
- *value* is the given arguments value if needed (optional). For instanse, "-v" doesn't have any value. 

Usage examples:
```python
# object creation
arg_maker = argument_maker()

# without value
arg_maker.add_arg("-vvv")

# with value
inventory_path = "/path/to/inventory"
arg_maker.add_arg("-i", inventory_path)

# --extra-vars example
extra_vars = {"jupyter_install": True, "spark_version": 2.4}
arg_maker.add_arg("--extra-vars", extra_vars)

```

After all of the needed actions, *argument_maker* object should be passed to runner class *init* method.


## runner

**\_\_init\_\_(pb_path, arg_maker, debug_lvl=None)**
- *pb_path* - path of the playbook .yaml file
- *arg_maker* - object of *argument_maker* class
- *debug_lvl* - currently this option is not for user purposes. It is planned that in future this option will this option will give usefull information for *cotea* user

### controlling interfaces

**has_next_play(): bool**

Checks if there is unexecuted *plays* in current Ansible execution. Returns *true* if there is.

**has_next_task(): bool**

Checks if there is unexecuted *tasks* in currently executing *play*. Returns *true* if there is.

**run_next_task(): []TaskResult**

Runs the next task and returns its results (a list of [TaskResult](https://github.com/ispras/cotea/blob/main/docs/cotea_docs.md#taskresult) class objects) on every host in current group. 

**finish_ansible()**

Starts a bunch of actions that are needed to finish the current Ansible execution.

These four interfaces are the main part of *cotea*. They let one control the execution of *ansible-playbook* launch. Every usage of cotea will contain them in the following order:
```python
# r = runner(...)

while r.has_next_play():
    while r.has_next_task():
        r.run_next_task()

r.finish_ansible()
```

**rerun_last_task()**

Queues the last running task for re-execution.

### debugging interfaces

**get_cur_play_name(): str**

Returns the current play name.

**get_next_task(): ansible.playbook.task.Task**

Returns the [ansible.playbook.task.Task](https://github.com/ansible/ansible/blob/devel/lib/ansible/playbook/task.py#L46) object of the next task.

**get_next_task_name(): str**

Returns the name of the next task.

**get_prev_task(): ansible.playbook.task.Task**

Returns the [ansible.playbook.task.Task](https://github.com/ansible/ansible/blob/devel/lib/ansible/playbook/task.py#L46) object of the previous task.

**get_prev_task_name(): str**

Returns the name of the previous task.

**get_last_task_result(): []TaskResult**

Returns a list with [TaskResult](https://github.com/ispras/cotea/blob/main/docs/cotea_docs.md#taskresult) objects where each element containes the results of the last task on each of the hosts of the current group.

**was_error(): bool**

Returns *true* if Ansible execution ends with an error.

**get_error_msg(): str**

Returns Ansible failure message (the last error msg that wasn't ignored).

**get_variable(var_name): str**

- *var_name* - the name of the requested variable

Returns the value of the Ansible variable with name *var_name*.


### TaskResult
This class stores the task results in a convenient way. Based on [ansible.executor.task_result.TaskResult](https://github.com/ansible/ansible/blob/devel/lib/ansible/executor/task_result.py#L25).

Fields:
- *result* - dict with keys like "stdout", "invocation", "changed", "failed" and so on
- *task_name* - the name of the task
- "task_ansible_object" - the copy of original object of [ansible.executor.task_result.TaskResult](https://github.com/ansible/ansible/blob/devel/lib/ansible/executor/task_result.py#L25)
- *task_fields* - dict that containes fields of the task (e.g. module arguments)
-  *is_changed* - True if task is "changed"
-  *is_failed* - True if task was failed
-  *is_skipped* - True if task was skipped
-  *is_unreachable* - True if "unreachable"
-  *stdout* - str that containes stdout of the executed task
-  *stderr* - str that containes stderr of the executed task
-  *msg* - str that containes message that is constructed by Ansible (for example, in the case of the fail of task, it containes the reason of failure)