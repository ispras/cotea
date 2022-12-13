# cotea interactive mode

In the case of task failure, cotea interactive mode can be activated by this [function]((https://github.com/ispras/cotea/blob/main/src/cotea/debug_utils.py#L47)):

**interactive_discotech(failed_task: ansible.playbook.task.Task, r: cotea.runner)**

How to undertand that some task was failed? The runner's run_next_task method returns list of [TaskResult](https://github.com/ispras/cotea/blob/main/docs/cotea_docs.md#taskresult) objects. Each TaskResult object has *is_failed* and *is_unreachable* fields. If some of these fields is true - task was failed. The object of the failed task (to pass it to a *interactive_discotech* function) can be obtained through *task_ansible_object* field of TaskResult object.

Below is a complete example of the interactive mode activation:
```python
r = runner(pb_path, am, show_progress_bar=True)

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
```

