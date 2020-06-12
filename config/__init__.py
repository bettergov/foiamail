import os
import yaml


class Config(object):
    def __init__(self, filename=None):
        if "/" in filename or "\\" in filename:
            raise ValueError("Config filenames should not contain paths!")
        basepath = os.path.abspath(os.path.dirname(__file__))
        self.filepath = os.path.join(basepath, filename)
        with open(self.filepath, "r") as f:
            self.data = yaml.safe_load(f)


config = Config(
    filename=os.environ.get("FOIAMAIL_CONFIG_FILENAME", "config.yaml")
)
