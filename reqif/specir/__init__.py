"""reqif.specir — ReqIF ↔ SpecIR interoperability.

Public API
----------
.. autofunction:: import_reqif
.. autofunction:: export_reqif
.. autofunction:: decompile
.. autofunction:: generate_model
.. autofunction:: generate_project
"""
from .decompiler import decompile
from .exporter import export_reqif, export_reqif_multi
from .importer import import_reqif
from .model_generator import generate_model
from .project_generator import generate_project

__all__ = [
    "import_reqif",
    "export_reqif",
    "export_reqif_multi",
    "decompile",
    "generate_model",
    "generate_project",
]
