class argument_maker:
    def __init__(self):
        self.args = []

    def add_arg(self, param_name, value=None):
        self.args.append(str(param_name))
        if value:
            self.args.append(str(value))


'''
    def get_args(self):
        return help_class(self.options)


class help_class(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
               setattr(self, a, [help_class(x) if isinstance(x, dict) else x for x in b])
            else:
               setattr(self, a, help_class(b) if isinstance(b, dict) else b)


default_options = {'listhosts': None, 'ssh_common_args': '', 'step': None, 'ask_vault_pass': False,
    'private_key_file': None, 'diff': False, 'args': ['test_playbook.yml'], 'timeout': 10,
    'extra_vars': [], 'become_method': 'sudo', 'connection': 'smart', 'vault_password_files': [],
    'module_path': None, 'become': False, 'check': False, 'flush_cache': None,
    'inventory': ['/home/steve/vagrant_practice/vagrant_getting_started/hosts'], 'skip_tags': [],
    'tags': ['all'], 'force_handlers': False, 'become_user': None, 'listtags': None, 'vault_ids': [],
    'forks': 5, 'scp_extra_args': '', 'subset': None, 'ask_pass': False, 'verbosity': 3, 'remote_user': None,
    'become_ask_pass': False, 'sftp_extra_args': '', 'start_at_task': None, 'syntax': None, 'listtasks': None,
    'ssh_extra_args': ''}
'''
