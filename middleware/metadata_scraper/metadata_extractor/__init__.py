"""
This package currently only consists of one public module: metadata_extractor
"""

from .metadata_extractor import *

# We need to also import these submodules as this is required by the registration process
from .metadata_extractor_embedded_jsonld import *
from .metadata_extractor_jsonld import *
