import re
import os
import pathlib
from dataclasses import dataclass
from typing import List

import tabulate
from argparse import ArgumentParser

# Типы файлов, что необходимо игнорировать при анализе
IGNORE_EXTENSIONS = [".svg", ".pyc"]


@dataclass
class FileInfo:
    lines: int = 0
    symbols: int = 0
    size: int = 0


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def format_bytes(size: int) -> str:
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "К", 2: "М", 3: "Г", 4: "Т"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}Б"


def get_gitignore(base_dir: pathlib.Path):
    """
    Ищем файл `.gitignore` и создаем список для игнорирования
    """

    gitignore_file = base_dir / ".gitignore"
    data = []  # Список для игнорирования

    if gitignore_file.exists():
        print(Colors.HEADER, "Найден файл .gitignore" + Colors.ENDC)

        with gitignore_file.open() as file:
            data = file.readlines()  # Считываем файлы

        for i, line in enumerate(data):
            if line.startswith("!"):
                # Пропускаем строки, которые указывают на файлы, что не нужно игнорировать
                data.remove(line)
                continue

            # Создаем из строки регулярное выражение
            line = "^" + line

            if line.endswith("/"):
                line = line[:-1]

            line = line.replace(".", r"\.")
            line = line.replace("*", ".*").replace("\n", "$")

            data[i] = line

    # По умолчанию игнорируем папки ".git", ".idea", "venv"
    return ["^\\.git$", "^\\.idea$", "^venv$"] + data


def find_files(base_dir: pathlib.Path, gitignore_list: list, result_files: list):
    """
    Ищем файлы и папки в base_dir
    """

    for p in base_dir.glob("*"):
        for gi in gitignore_list:
            if re.findall(re.compile(gi), p.as_posix()):
                break
        else:
            if p.is_file():
                result_files.append(p)  # Добавляем файл

            elif p.is_dir():
                # Рекурсивно ищем в папке файлы
                find_files(p, gitignore_list, result_files)


def inspect_file(file: pathlib.Path) -> FileInfo:
    """
    Сканируем файл для анализа
    """

    file_info = FileInfo()

    if file.suffix in IGNORE_EXTENSIONS:
        return file_info

    file_info.size = file.stat().st_size

    try:
        with file.open(encoding="utf8") as f:
            data = f.readlines()
    except UnicodeDecodeError:
        return file_info

    for line in data:
        file_info.symbols += len(re.findall(r"\S", line))

        if file.suffix == ".py" and re.match(r"^\s*#|^\s*$", line):
            continue
        elif file.suffix == ".js" and re.match(r"^\s*//|^\s*$", line):
            continue
        elif re.match(r"^\s*$", line):
            continue

        file_info.lines += 1

    return file_info


def scan_files(files: List[pathlib.Path]):
    files_types = {}

    for file in files:
        # Начинаем сканировать файлы

        if not file.suffix:
            continue  # Пропускаем файлы без суффикса

        files_types.setdefault(file.suffix, {})

        file_info: FileInfo = inspect_file(file)

        for key in ["lines", "symbols", "size"]:
            # Для определенного типа файла добавляем данные
            files_types[file.suffix][key] = files_types[file.suffix].get(key, 0) + getattr(file_info, key)

        # Увеличиваем кол-во файлов данного типа на один
        files_types[file.suffix]["count"] = files_types[file.suffix].get("count", 0) + 1

    return files_types


def start_scan(base_dir: pathlib.Path, use_gitignore: bool = True):
    """Точка входа"""

    print(
        Colors.OKGREEN,
        "🔎 Начинаем сканировать директорию",
        base_dir.absolute().as_posix() + Colors.ENDC,
    )
    os.chdir(base_dir)  # Переходим в директорию для сканирования
    base_dir = pathlib.Path(".")  # Используем новую директорию как точку входа

    files_to_scan = []

    # Список с файлами и папками, что надо проигнорировать
    gitignore_list = get_gitignore(base_dir) if use_gitignore else ["^\\.git$", "^\\.idea$"]

    # Ищем файлы
    find_files(base_dir, gitignore_list, files_to_scan)

    files_scan_result = scan_files(files_to_scan)

    output = []
    # Общее кол-во строк
    lines_total_sum = sum([v["lines"] for v in files_scan_result.values()])
    # Общее кол-во символов
    symbols_total_sum = sum([v["symbols"] for v in files_scan_result.values()])
    # Общий размер
    total_size = sum([v["size"] for v in files_scan_result.values()])

    for suffix, val in files_scan_result.items():
        lines_percent = round(val["lines"] * 100 / lines_total_sum, 2)
        symbols_percent = round(val["symbols"] * 100 / symbols_total_sum, 2)

        # Добавляем данные для вывода
        # тип файла, кол-во файлов, кол-во линий, процент, кол-во символов, процент
        output.append(
            [
                suffix,
                val["count"],
                val["lines"],
                lines_percent,
                val["symbols"],
                symbols_percent,
                format_bytes(val["size"]),
            ]
        )

    # Сортируем строки по кол-ву файлов (по убыванию)
    # Если кол-во одинаковое, то по кол-ву линий (по убыванию)
    output = sorted(output, key=lambda x: x[2], reverse=True)  # Сначала по кол-ву строк
    output = sorted(output, key=lambda x: x[1], reverse=True)  # Затем по кол-ву файлов

    # Вывод итоговой таблицы
    print()
    print(
        tabulate.tabulate(
            output,
            headers=["Тип файла", "Файлов", "Строчек", "%", "Символов", "%", "Размер"],
        )
    )
    print(f"Общее кол-во строк:    {lines_total_sum}")
    print(f"Общее кол-во символов: {symbols_total_sum}")
    print(f"Общий размер:          {format_bytes(total_size)}")


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
