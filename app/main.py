"""Entry point for Efsal application."""

import sys

from app.application import EfsalApp


def main():
    """Launch the Efsal application."""
    app = EfsalApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
