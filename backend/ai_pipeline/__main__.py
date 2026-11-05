"""Entry point for CLI."""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "cli":
    # Remove 'cli' from argv for argparse
    sys.argv.pop(1)
    from ai_pipeline.cli import main
    main()
else:
    print("Usage: python -m ai_pipeline cli [--backend BACKEND] [--max-steps STEPS]")
    sys.exit(1)
