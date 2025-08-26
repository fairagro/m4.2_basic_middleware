"""
This package currently only consists of one public module: metadata_extractor
"""

from .metadata_extractor import * # noqa: F403

# We need to also import these submodules as this is required by the registration process
from .metadata_extractor_embedded_jsonld import * # noqa: F403
from .metadata_extractor_jsonld import * # noqa: F403
