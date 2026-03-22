"""Allow ``python -m reqif.specir`` to invoke the CLI."""
from .cli import main

raise SystemExit(main())
