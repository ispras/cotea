def remove_modules_from_imported(module_name_like, not_to_delete=None):
    import sys

    for module in list(sys.modules):
        if module_name_like in module:
            if not_to_delete is not None:
                if not_to_delete in module:
                    continue
            
            sys.modules.pop(module)

#  True, ""           - if has
#  False, "error msg" - if hasn't
def obj_has_attrs(obj, attrs_list):
    for attr in attrs_list:
        if not hasattr(obj, attr):
            error_msg = "Obj {} doesn't have attr {} but should"
            return False, error_msg.format(obj, attr)
    
    return True, ""