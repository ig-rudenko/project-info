import pathlib
from argparse import ArgumentParser

from scanner.formats import Colors
from scanner.scanner import start_scan


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Сканирует директорию, ищет файлы",
        usage="%(prog)s [--full] directory",
    )
    parser.add_argument(
        "--full",
        action="store_const",
        const=True,
        default=False,
        help="Фильтровать по .gitignore файлу, если он имеется",
    )
    parser.add_argument("directory", help="Путь до папки с проектом")
    args = parser.parse_args()

    try:
        start_scan(pathlib.Path(args.directory), not args.full)
    except KeyboardInterrupt:
        print(Colors.WARNING, "\nОстановка", Colors.ENDC)
