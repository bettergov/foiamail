import os
import sys
import yaml


class Config(object):
    def __init__(self, filename=None):
        if "/" in filename or "\\" in filename:
            raise ValueError("Config filenames should not contain paths!")
        basepath = os.path.abspath(os.path.dirname(__file__))
        self.filepath = os.path.join(basepath, filename)

        # This needs to run before things try to load config.yaml
        if not os.path.exists(self.filepath):
            print("Error: %s does not exist!" % (self.filepath))
            print("Copy the example configuration file, config/config.example.yaml, and edit any settings you'd like to change before proceeding.")
            sys.exit(1)



        with open(self.filepath, "r") as f:
            self.data = yaml.safe_load(f)


config = Config(
    filename=os.environ.get("FOIAMAIL_CONFIG_FILENAME", "config.yaml")
)
