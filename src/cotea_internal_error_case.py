import shutil
import unittest


class TestCotea(unittest.TestCase):

    def tearDown(self) -> None:
        from cotea.utils import remove_modules_from_imported

        # Remove any Ansible-related objects from memory
        #   to clear previous execution context
        remove_modules_from_imported(module_name_like="cotea")

    def test_incorrect_playbook_path_case(self):
        from cotea.runner import runner
        from cotea.arguments_maker import argument_maker

        pb_path = "cotea_run_files/#%|&"
        inv_path = "cotea_run_files/inv"

        arg_maker = argument_maker()
        arg_maker.add_arg("-i", inv_path)
        r = runner(pb_path, arg_maker, show_progress_bar=True)

        try:
            while r.has_next_play():
                while r.has_next_task():
                    r.run_next_task()
            r.finish_ansible()
        except Exception as e:
            r.finish_ansible()
            self.assertTrue(hasattr(e, "message"), msg="Exception is expected to have 'message' attribute")
            self.assertTrue(e.message.startswith(f"the playbook: {pb_path} could not be found"),
                            msg="Unexpected exception message")
        else:
            self.assertFalse(True, msg="Ansible is supposed to fail due to syntax error "
                                       "and its' exception should be passed to main thread")

    def test_incorrect_syntax_case(self):
        from cotea.runner import runner
        from cotea.arguments_maker import argument_maker

        pb_path = "cotea_run_files/incorrect.yaml"
        inv_path = "cotea_run_files/inv"

        arg_maker = argument_maker()
        arg_maker.add_arg("-i", inv_path)
        r = runner(pb_path, arg_maker, show_progress_bar=True)

        try:
            while r.has_next_play():
                while r.has_next_task():
                    r.run_next_task()
            r.finish_ansible()
        except Exception as e:
            r.finish_ansible()
            # NOTE: e should be AnsibleParserError, but "isinstance" returns False for some reason
            self.assertTrue(hasattr(e, "message"), msg="Exception is expected to have 'message' attribute")
            self.assertTrue(e.message.startswith("couldn't resolve module/action"),
                            msg="Unexpected exception message")
        else:
            self.assertFalse(True, msg="Ansible is supposed to fail due to syntax error "
                                       "and its' exception should be passed to main thread")


if __name__ == '__main__':
    unittest.main()
