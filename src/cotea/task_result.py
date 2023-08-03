from ansible.executor.task_result import TaskResult as TR


class TaskResult:
    def __init__(self, ansible_task_result: TR):
        self.result = ansible_task_result._result.copy()
        self.task_name = str(ansible_task_result.task_name)
        self.task_ansible_object = ansible_task_result._task
        self.task_fields = ansible_task_result._task_fields.copy()

        self.original_task_uuid = ""
        if hasattr(ansible_task_result._task, "_uuid"):
            self.original_task_uuid = ansible_task_result._task._uuid

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
        else:
            msg = self.result.get("message")
            if msg:
                self.msg = str(msg)


    def pretty_string(self):
        task_info = "&&&&&&&&&&&&&&&&&&&&&&&&&&&&\n"
        task_info += "Task with name {}\n"
        task_info += "is_changed - {}\n"
        task_info += "is_failed - {}\n"
        task_info += "is_skipped - {}\n"
        task_info += "is_unreachable - {}\n"
        task_info += "stdout - {}\n"
        task_info += "stderr - {}\n"
        task_info += "msg - {}\n"
        task_info += "result dict - {}\n"
        task_info += "task fields - {}\n"

        task_info += "\n"

        task_info = task_info.format(
            self.task_name,
            self.is_changed,
            self.is_failed,
            self.is_skipped,
            self.is_unreachable,
            self.stdout,
            self.stderr,
            self.msg,
            str(self.result),
            str(self.task_fields)
        )

        t = self.task_ansible_object
        d = dir(t)
        
        for attr in d:
            task_info += "{} - {}\n".format(attr, getattr(t, attr))

        task_info += "&&&&&&&&&&&&&&&&&&&&&&&&&&&&\n"

        return task_info
        