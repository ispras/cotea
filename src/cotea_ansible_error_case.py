import unittest

from cotea.runner import runner
from cotea.arguments_maker import argument_maker


def run_ansible_error_case(pb_path, inv_path):
    msg = ""

    arg_maker = argument_maker()
    arg_maker.add_arg("-i", inv_path)

    r = runner(pb_path, arg_maker, show_progress_bar=True)

    while r.has_next_play():
        while r.has_next_task():
            r.run_next_task()

    r.finish_ansible()

    if r.was_error():
        return True
    
    return False


def run_ansible_error_case_with_ignore(pb_path, inv_path):
    msg = ""

    arg_maker = argument_maker()
    arg_maker.add_arg("-i", inv_path)

    r = runner(pb_path, arg_maker, show_progress_bar=True)

    while r.has_next_play():
        while r.has_next_task():
            r.run_next_task()

            r.ignore_errors_of_next_task()

    r.finish_ansible()

    if r.was_error():
        return True
    
    return False


class TestCotea(unittest.TestCase):
    def test_ansible_task_error_case(self):
        pb_path = "cotea_run_files/error.yaml"
        inv_path = "cotea_run_files/inv"

        was_exception = False
        exception_msg = None

        was_error_in_tests = False
        test_fail_msg = None

        try:
            was_error_in_tests = run_ansible_error_case(pb_path, inv_path)
        except Exception as e:
            was_exception = True
            exception_msg = str(e)
        
        self.assertFalse(was_exception, msg=exception_msg)

        msg = "Ansible should be failed, there was an error in playbook, but cotea didn't catch that"
        self.assertTrue(was_error_in_tests, msg=msg)

        try:
            was_error_in_tests = run_ansible_error_case_with_ignore(pb_path, inv_path)
        except Exception as e:
            was_exception = True
            exception_msg = str(e)
        
        self.assertFalse(was_exception, msg=exception_msg)

        msg = "runner.ignore_errors_of_next_task works wrong. The Ansible task failure wasn't ignored"
        self.assertFalse(was_error_in_tests, msg=msg)



if __name__ == '__main__':
    unittest.main()