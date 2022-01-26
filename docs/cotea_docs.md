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

**\_\_init\_\_(pb_path, arg_maker=None, debug_lvl=None, log_f=None)**
- *pb_path* - path of the playbook .yaml file
- *arg_maker* - object of *argument_maker* class
- *debug_lvl* - currently this option is not for user purposes. It is planned that in future this option will this option will give usefull information for *cotea* user
- *log_f* - path to file to which all the *cotea* output will be redirected. cotea output means the standard Ansible output with the *cotea* additional messages. This option can be useful when one embeds Ansible into another system. The system's output will not contain Ansible output in this case.

### controlling interfaces

**has_next_play(): bool**
Checks if there is unexecuted *plays* in current Ansible execution. Returns *true* if there is.

**setup_play_for_run(): bool**
Starts a bunch of actions that are needed to setup play for run. Returns, when play is ready to run (returns *true*). If there was an error and *play* is not ready to start, returns *false*.

**has_next_task(): bool**
Checks if there is unexecuted *tasks* in currently executing *play*. Returns *true* if there is.

**run_next_task()**
Runs the next *task* in the currently executing *play*. 

**finish_ansible()**
Starts a bunch of actions that are needed to finish the current Ansible execution. This method has to be called only when there are no unexecuted *plays* and *tasks* (has_next_play and has_next_task return *false*).

These five interfaces are the main part of *cotea*. They let one control the execution of *ansible-playbook* launch. Every usage of cotea will contain them in the following order:
```python
# r = runner(...)

while r.has_next_play():
    setup_ok = r.setup_play_for_run()
    
	if setup_ok:
		while r.has_next_task():
			r.run_next_task()

r.finish_ansible()
```

**skip_next_task()**
Skips the next tasks of currently executing play.

### debugging interfaces
**get_variable(var_name): str**
- *var_name* - the name of the requested variable

Returns value of the Ansible variable with name *var_name*.

**was_error(): bool**
Returns *true* if Ansible execution ends with an error.

**get_error_msg(): str**
If Ansible execution ends with an error(*was_error* returns *true*), returns error message.

**get_cur_play_name(): str**
Returns the current play name.

**get_next_task_name(): str**
Returns the next task name.

**get_last_results(): []ansible.executor.task_result**
Return a list with results of the last executed task on every host of the currently executing play. Results are objects of the Ansible class [TaskResult](https://github.com/ansible/ansible/blob/devel/lib/ansible/executor/task_result.py#L25). 

**get_results(): []ansible.executor.task_result**
Returns a list of task results which were obtained during the entire execution (at the calling moment). Results are objects of the Ansible class [TaskResult](https://github.com/ansible/ansible/blob/devel/lib/ansible/executor/task_result.py#L25). 

