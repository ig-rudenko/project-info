import pathlib

from .formats import Colors

# Типы файлов, что необходимо игнорировать при анализе
IGNORE_EXTENSIONS = [".svg", ".pyc"]
IGNORE_FILENAMES = ["pyproject.toml", "poetry.lock", "requirements.txt", "mypy.ini"]
IGNORE_DEFAULT = ["^\\.git$", "^\\.idea$", "^venv$"]


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
    return IGNORE_DEFAULT + data
