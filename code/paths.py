import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset(*parts):
    """Путь к ресурсу в корне проекта (images/, sounds/, fonts/)."""
    return os.path.join(PROJECT_ROOT, *parts)


def data(*parts):
    """Путь к файлу в data/."""
    return os.path.join(PROJECT_ROOT, "data", *parts)