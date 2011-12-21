import ConfigParser
import io

default_config = """
[pixelpipeline]
verbose: false
"""

cfg = ConfigParser.SafeConfigParser()
cfg.readfp(io.BytesIO(default_config))
