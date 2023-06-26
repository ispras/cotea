def generate_error_msg(method_name, should_be, returned):
    return "{} worked wrong\nshould be {}, returned {}".format(method_name, should_be, returned)