import ConfigParser
import io, os

default_config = """
[pixelpipeline]
verbose: false
"""

cfg = ConfigParser.SafeConfigParser()
cfg.readfp(io.BytesIO(default_config))
userConfig = os.path.expanduser("~/.voluminarc")
if os.path.exists(userConfig):
    cfg.read(userConfig)
