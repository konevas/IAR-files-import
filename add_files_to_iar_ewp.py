import os
import argparse
from lxml import etree
from fnmatch import fnmatch
from typing import Iterable
from typing import Dict

NAME_TAG = "name"
GROUP_TAG = "group"
FILE_TAG = "file"
IAR_PROJECT_DIR = "$PROJ_DIR$"


def get_next_file_path(project_path: str,
                       files_directory_path: str,
                       pattern: str = "*.*") -> Iterable[str]:
    """
    Generates file relative path
    :param project_path: absolute path to project
    :param files_directory_path: absolute path to directory with files
    :param pattern: Unix filename pattern matching
    :return: file generator
    """
    for p, dir_list, file_list in os.walk(files_directory_path):
        for f in file_list:
            if fnmatch(f, pattern):
                yield os.path.join(os.path.relpath(p, project_path), f)


def get_xpath(tag: str, name: str) -> str:
    """
    Get the xpath to the element with the given name
    :param tag: element tag
    :param name: subelement containing the text with element name
    :return: xpath
    """
    return f".//name[text() = '{name}']/parent::{tag}"


def get_iar_file_text(file_relative_path: str) -> str:
    """
    Get the file description text for name element
    :param file_relative_path: relative to project directory path to file
    :return: text for name element
    """
    return os.path.join(IAR_PROJECT_DIR, file_relative_path)


def append_child(element: object, tag: object, name: str) -> object:
    """
    Append a new element to a tree
    :param element: element to append as child to
    :param tag: tag name
    :param name: object name
    :return: newly appended element
    """
    new_element = etree.SubElement(element, tag)
    etree.SubElement(new_element, NAME_TAG).text = name

    return new_element


def write_tree(tree: object, path: str, encoding="iso-8859-1", pretty=True):
    """
    Write the tree to a file
    :param tree: lxml ElementTree or element
    :param path: path to the file
    :param encoding: file encoding
    :return: None
    """
    etree.indent(tree)
    with open(path, 'wb') as proj:
        proj.write(etree.tostring(tree,
                                  encoding=encoding,
                                  pretty_print=pretty))


def add_file(tree: object, file_relative_path: str) -> None:
    """
    Adds a file to a tree
    :param tree: ElementTree or element
    :param file_relative_path: file relative to project directory path
    :return: None
    """
    print("* " + file_relative_path)
    dir_path, file = os.path.split(file_relative_path)
    context = tree
    element = None
    for name in dir_path.split('\\'):
        try:
            element = context.xpath(get_xpath(GROUP_TAG, name))[0]
        except IndexError:
            print(f"{name} from {dir_path} not found. Adding it to the tree")
            element = append_child(context, GROUP_TAG, name)
        except Exception as e:
            print("Fatal error: " + str(e))
            exit(-1)
        context = element
        print("* Context is at " + name)

    if not context.xpath(get_xpath(FILE_TAG, file)):
        append_child(context,
                     FILE_TAG,
                     get_iar_file_text(file_relative_path))
        print("Added" + " " + file_relative_path)


def add_files_to_tree(tree: object, files: Iterable[str]) -> None:
    """
    Adds files to a tree
    :param tree: lxlm ElementTree or Element
    :param files: iterable with files relative to project directory path
    :return:
    """
    for file_path in files:
        add_file(tree, file_path)


def main(args: Dict[str, str]) -> None:
    project_path = args[PROJECT_PATH_ID]
    files_dir_path = args[PATH_ID]
    pattern = args[PATTERN_ID]

    project_dir, project_name = os.path.split(project_path)
    root = etree.parse(project_path).getroot()
    add_files_to_tree(root,
                      get_next_file_path(project_dir, files_dir_path, pattern))
    write_tree(root, project_path, "iso-8859-1")


if __name__ == '__main__':
    PATH_ID = "Path"
    PATTERN_ID = "Pattern"
    PROJECT_PATH_ID = "Project_dir"
    FIND_ALL_FILES = "*.*"

    parser = argparse.ArgumentParser(description="Import the files into the "
                                                 "IAR project file following "
                                                 "the directory tree.")

    parser.add_argument(PATH_ID,
                        metavar='<path>',
                        type=str,
                        help='A path to the source directory to be added')

    parser.add_argument(PROJECT_PATH_ID,
                        metavar='<project_path>',
                        type=str,
                        help='A path to the project.')

    parser.add_argument("-p",
                        "--pattern",
                        type=str,
                        help='Unix filename pattern matching',
                        default=FIND_ALL_FILES,
                        dest=PATTERN_ID)

    main(vars(parser.parse_args()))
