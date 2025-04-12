from .utils import extract_file_info
from .freemind import FreemindParser
from .markdown import MarkdownParser


def get_parser(path: str):
    name, extension = extract_file_info(path)
    if extension == ".mm":
        return FreemindParser()
    elif extension == ".md":
        return MarkdownParser()

    raise NotImplementedError(f"Not suitable parse for {name}{extension}")
