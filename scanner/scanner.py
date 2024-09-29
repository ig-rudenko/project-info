import os
import pathlib
import re
from typing import List

import tabulate

from .types import FileInfo, ScanResult
from .formats import format_bytes, Colors
from .ignores import IGNORE_EXTENSIONS, IGNORE_FILENAMES, get_gitignore


def find_files(base_dir: pathlib.Path, gitignore_list: list, result_files: list) -> None:
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

    if file.name in IGNORE_FILENAMES:
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


def scan_files(files: List[pathlib.Path]) -> dict[str, ScanResult]:
    files_types: dict[str, ScanResult] = {}

    for file in files:
        # Начинаем сканировать файлы

        if not file.suffix:
            continue  # Пропускаем файлы без суффикса

        files_types.setdefault(file.suffix, ScanResult.create_empty())
        file_info: FileInfo = inspect_file(file)

        files_types[file.suffix].lines += file_info.lines
        files_types[file.suffix].symbols += file_info.symbols
        files_types[file.suffix].size += file_info.size

        # Увеличиваем кол-во файлов данного типа на один
        files_types[file.suffix].count += 1

    return files_types


def start_scan(base_dir: pathlib.Path, use_gitignore: bool = True):
    """Точка входа"""

    print(
        Colors.OKGREEN,
        "🔎 Начинаем сканировать директорию",
        base_dir.resolve().absolute().as_posix() + Colors.ENDC,
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
    lines_total_sum = sum([v.lines for v in files_scan_result.values()])
    # Общее кол-во символов
    symbols_total_sum = sum([v.symbols for v in files_scan_result.values()])
    # Общий размер
    total_size = sum([v.size for v in files_scan_result.values()])

    for suffix, val in files_scan_result.items():
        lines_percent = round(val.lines * 100 / lines_total_sum, 2)
        symbols_percent = round(val.symbols * 100 / symbols_total_sum, 2)

        # Добавляем данные для вывода
        # тип файла, кол-во файлов, кол-во линий, процент, кол-во символов, процент
        output.append(
            [
                suffix,
                val.count,
                val.lines,
                lines_percent,
                val.symbols,
                symbols_percent,
                format_bytes(val.size),
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
    print(f"Общее кол-во строк:    {lines_total_sum:,d}".replace(",", " "))
    print(f"Общее кол-во символов: {symbols_total_sum:,d}".replace(",", " "))
    print(f"Общий размер:          {format_bytes(total_size)}")
