def remove_modules_from_imported(module_name_like, not_to_delete=None):
    import sys

    for module in list(sys.modules):
        if module_name_like in module:
            if not_to_delete is not None:
                if not_to_delete in module:
                    continue
            
            sys.modules.pop(module)