import unittest

from cotea.runner import runner
from cotea.arguments_maker import argument_maker
from cotea_test_utils import generate_error_msg


# almost every cotea's function(method) is strongly connected
# with Ansible launch and at the moment we didn't 
# implement normal testing scheme (including unit testing and etc)
def run_cotea_ok_case(pb_path, inv_path):
    msg = ""
    play_names = ["Play1", "Play2"]
    plays_tasks = []
    
    play1_tasks = ["Gathering Facts", "meta", "Pinge Ponge", "Creates directory",
                    "Creating an empty file", "Delete file",
                    "Delete content & directory", "meta", "meta", "None"]
    plays_tasks.append(play1_tasks)
    
    play2_tasks = ["Gathering Facts", "meta", "Pinge Ponge", "meta", "meta", "None"]
    plays_tasks.append(play2_tasks)

    arg_maker = argument_maker()
    arg_maker.add_arg("-i", inv_path)

    r = runner(pb_path, arg_maker, show_progress_bar=True)
    plays_ind = 0
    tasks_ind = 0

    while r.has_next_play():
        tasks_ind = 0
        play_name = r.get_cur_play_name()

        if play_name != play_names[plays_ind]:
            msg = generate_error_msg("runner.get_cur_play", play_names[plays_ind], play_name)
            r.finish_ansible()
            return True, msg

        while r.has_next_task():
            next_task_name = r.get_next_task_name()
            next_task_name_should_be = plays_tasks[plays_ind][tasks_ind]

            if next_task_name != next_task_name_should_be:
                msg = generate_error_msg("runner.get_next_task_name", next_task_name_should_be, next_task_name)
                r.finish_ansible()
                return True, msg
            
            if tasks_ind > 0:
                prev_task_name = r.get_prev_task_name()
                prev_task_name_should_be = plays_tasks[plays_ind][tasks_ind - 1]

                if prev_task_name != prev_task_name_should_be:
                    msg = generate_error_msg("runner.get_prev_task_name", prev_task_name_should_be, next_task_name)
                    r.finish_ansible()
                    return True, msg

            r.run_next_task()

            prev_task_name = r.get_prev_task_name()
            if prev_task_name != next_task_name_should_be:
                msg = generate_error_msg("runner.get_prev_task_name", next_task_name_should_be, prev_task_name)
                r.finish_ansible()
                return True, msg

            tasks_ind += 1
        
        plays_ind += 1

    r.finish_ansible()

    if r.was_error():
        ansible_err_msg = r.get_error_msg()
        msg += "\nAnsible task error:\n{}".format(ansible_err_msg)
        return True, msg
    
    return False, msg


class TestCotea(unittest.TestCase):
    def test_cotea_ok_case(self):
        pb_path = "cotea_run_files/ok.yaml"
        inv_path = "cotea_run_files/inv"

        was_exception = False
        exception_msg = None

        was_error_in_tests = False
        test_fail_msg = None

        try:
            was_error_in_tests, test_fail_msg = run_cotea_ok_case(pb_path, inv_path)
        except Exception as e:
            was_exception = True
            exception_msg = str(e)
        
        self.assertFalse(was_exception, msg=exception_msg)
        self.assertFalse(was_error_in_tests, msg=test_fail_msg)


if __name__ == '__main__':
    unittest.main()