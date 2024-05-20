import os
import configparser
import cotea.consts as consts


class cotea_config:
    def __init__(self):
        self.conf = {}

        # default values
        self.conf["continue_on_fail"] = False
    

    def load_from_file(self, config_path):
        if os.path.isfile(config_path):
            confparser_obj = configparser.ConfigParser()
            confparser_obj.read(config_path)
            section_name = consts.COTEA_CONFIG_SECTION_NAME
            
            if section_name in confparser_obj:
                section = confparser_obj[section_name]

                for key in self.conf:
                    if key in section:
                        value = section[key]

                        if value == "True":
                            value = True
                        elif value == "False":
                            value = False
                        
                        self.conf[key] = value
        
        
    def get_conf_param(self, param_name):
        if param_name in self.conf:
            return self.conf[param_name]
        
        return None