from ansible.executor.task_result import TaskResult as TR


class TaskResult:
    def __init__(self, ansible_task_result: TR):
        self.result = ansible_task_result._result.copy()
        self.task_name = str(ansible_task_result.task_name)
        self.task_ansible_object = ansible_task_result._task.copy()
        self.task_fields = ansible_task_result._task_fields.copy()

        self.is_changed = ansible_task_result.is_changed()
        self.is_failed = ansible_task_result.is_failed()
        self.is_skipped = ansible_task_result.is_skipped()
        self.is_unreachable = ansible_task_result.is_unreachable()

        self.stdout = ""
        stdout = self.result.get("stdout")
        if stdout:
            self.stdout = str(stdout)
        
        self.stderr = ""
        stderr = self.result.get("stderr")
        if stderr:
            self.stderr = str(stderr)

        self.msg = ""
        msg = self.result.get("msg")
        if msg:
            self.msg = str(msg)

