#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "busca_comissoes_cd.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - bootstrap helper
        raise ImportError(
            "Django não está instalado ou não pôde ser importado."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
