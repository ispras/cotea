from ansible.playbook.task import Task
from cotea.runner import runner


def print_help_msg():
    help_msg = "Informative commands:\n"
    help_msg += "'ft' - print info about the Failed Task\n"
    help_msg += "'msg' - print all ansible error MSGs (including the ignored ones)\n"
    help_msg += "'p' - print Progress bar\n"
    help_msg += "'h'/'help' - print this msg\n"
    help_msg += "\nAction commands:\n"
    help_msg += "'re' - RErun of the failed task\n"
    help_msg += "'v' - add new Variable as extra var\n"
    help_msg += "'c' - Continue ansible execution (go to the next task)\n"
    help_msg += "'nt' - add New Task\n"
    help_msg += "'w' - Watch ansible variable value\n"
    #help_msg += "'f' - Finish ansible execution\n"

    print(help_msg)


def pretty_print_task(task: Task):
    pretty_print = "Name: {}\nAction: {}\nArgs: {}\nbecome: {}\n".format(task.name,
                                                                         task.action,
                                                                         task.args,
                                                                         task.become)
    
    
    pretty_print_p2 = "Connection: {}\ndelegate_facts: {}\nenvironment: {}\n".format(task.connection,
                                                                                     task.delegate_facts,
                                                                                     task.environment)

    pretty_print += pretty_print_p2

    pretty_print_p2 = "delegate_facts: {}\nvars: {}\n".format(task.delegate_facts,
                                                              task.get_vars())
    pretty_print += pretty_print_p2

    pretty_print_p2 = "port: {}\nremote_user: {}\nretries: {}\ntags: {}\n".format(task.port,
                                                                                  task.remote_user,
                                                                                  task.retries,
                                                                                  task.tags)
    pretty_print += pretty_print_p2

    print(pretty_print)


def interactive_discotech(failed_task: Task, r: runner):
    print("\nINTERACTIVE MODE")
    
    while True:
        print("Enter command: ", end="")
        command = input()
        if command == "ft":
            pretty_print_task(failed_task)

        elif command == "re":
            r.rerun_last_task()
            r.progress_bar.add_to_total_task_count(1)
            break

        elif command == "msg":
            info_msg = "This msg list includes msg's that were ignored. "
            info_msg += "Msg's will be displayed in order of occurrence.\n"
            print(info_msg)

            err_msgs = r.get_all_error_msgs()
            msg_number = 1
            
            for msg in err_msgs:
                print("MSG number {}:\n{}\n".format(msg_number, msg))
                msg_number += 1

        elif command == "v":
            print("var will be added as extra var")
            print("Enter var name: ", end="")
            var_name = input()
            print("Enter var value: ", end="")
            var_value = input()
                                
            r.add_var_as_extra_var(var_name, var_value)
            print("var added successfully!\n")
        
        elif command == "c":
            break

        elif command == "p":
            print()
            play_name = r.get_cur_play_name()
            next_task = r.get_next_task_name()
            r.progress_bar.print_bar(play_name, next_task)
        
        elif command == "nt":
            print("Enter new task like a string entering all \\n and spaces needed:")
            new_task_str = input()

            # TODO: not sure that this is a good solution
            #       however, this is interactive mode and
            #       we always can say to user that he is wrong
            new_task_str = new_task_str.replace("\\n", "\n")
            add_ok, err_msg = r.add_new_task(new_task_str)

            if not add_ok:
                print("\nThe adding process was failed with the error:\n", err_msg)
            else:
                print("\nNew task was added! It will run on every host of current inventory.")
                print("Press 'c' after this, not 're'. This will run new task and the failed one after it.\n")
                r.progress_bar.add_to_total_task_count(1)
        
        elif command == "w":
            print("Enter var name: ", end="")
            
            var_name = input()
            value = r.get_variable(var_name)
            msg = "{} var value:\n{}".format(var_name, value)
            
            print(msg)

        elif command == "help" or command == "h":
            print_help_msg()

        else:
            print("Enter commands correctly! 'help' or just 'h' will help you\n")
