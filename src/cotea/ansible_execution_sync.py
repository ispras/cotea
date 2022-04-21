import threading


class ans_sync:
    def __init__(self, logger):
        self.runner_event = threading.Event()
        self.ansible_event = threading.Event()
        self.logger = logger
        self.curr_breakpoint_label = None

    def status(self):
        self.logger.debug("Runner event status: %s", self.runner_event.is_set())
        self.logger.debug("Ansible event status: %s",
                         self.ansible_event.is_set())

    def runner_just_wait(self):
        #self.logger.debug("runner: waiting...")
        self.runner_event.wait()
        self.runner_event.clear()

    def ansible_just_wait(self):
        #self.logger.debug("ansible: waiting...")
        self.ansible_event.wait()
        self.ansible_event.clear()

    def continue_runner_with_stop(self, curr_breakpoint_label):
        #self.logger.debug("ansible: resume runner work and wait")
        self.curr_breakpoint_label = curr_breakpoint_label
        self.runner_event.set()
        self.ansible_event.wait()
        self.ansible_event.clear()

    def continue_ansible_with_stop(self):
        #self.logger.debug("runner: resume ansible work and wait")
        self.ansible_event.set()
        self.runner_event.wait()
        self.runner_event.clear()
        #self.logger.debug("runner: ANSIBLE WAKED ME UP")

    def continue_runner(self):
        #self.logger.debug("ansible: resume runner work")
        self.runner_event.set()

    def continue_ansible(self):
        #self.logger.debug("runner: resume ansible work")
        self.ansible_event.set()
