import os

TEST_DIR = os.path.dirname(__file__)
ANSIBLE_DIR = os.path.join(TEST_DIR, "ansible")
INVENTORY_PATH = os.path.join(ANSIBLE_DIR, "docker.ini")


def generate_error_msg(method_name, should_be, returned):
    return "{} worked wrong\nshould be {}, returned {}".format(method_name, should_be, returned)