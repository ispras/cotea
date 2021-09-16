import threading


class ans_sync:
    def __init__(self, logger):
        self.runner_event = threading.Event()
        self.ansible_event = threading.Event()
        self.logger = logger

    def status(self):
        self.logger.info("Runner event status: %s", self.runner_event.is_set())
        self.logger.info("Ansible event status: %s",
                         self.ansible_event.is_set())

    def runner_just_wait(self):
        self.logger.info("runner: waiting...")
        self.runner_event.wait()
        self.runner_event.clear()

    def ansible_just_wait(self):
        self.logger.info("ansible: waiting...")
        self.ansible_event.wait()
        self.ansible_event.clear()

    def continue_runner_with_stop(self):
        self.logger.info("ansible: resume runner work and wait")
        self.runner_event.set()
        self.ansible_event.wait()
        self.ansible_event.clear()

    def continue_ansible_with_stop(self):
        self.logger.info("runner: resume ansible work and wait")
        self.ansible_event.set()
        self.runner_event.wait()
        self.runner_event.clear()
        self.logger.debug("runner: ANSIBLE WAKED ME UP")

    def continue_runner(self):
        self.logger.info("ansible: resume runner work")
        self.runner_event.set()

    def continue_ansible(self):
        self.logger.info("runner: resume ansible work")
        self.ansible_event.set()
