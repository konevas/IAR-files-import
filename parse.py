import os
from lxml import etree
import argparse
from fnmatch import fnmatch

NAME_TAG = "name"
GROUP_TAG = "group"
FILE_TAG = "file"
IAR_PROJECT_DIR = "$PROJ_DIR$"


def walk_through_files(project_path, path=".", pattern="*.*"):
    for p, dir_list, file_list in os.walk(path):
        for f in file_list:
            if fnmatch(f, pattern):
                yield os.path.join(os.path.relpath(p, project_path), f)


def print_name_recursive(element, tag):
    print(tag)
    for e in element:
        if e.tag == "name":
            print("  " + e.tag + ":" + e.text)
        else:
            print_name_recursive(e, e.tag)


def get_xpath(tag: str, name: str) -> str:
    return f"//name[text() = '{name}']/parent::{tag}"


def get_element(tag: str, name: str) -> etree.Element:
    """
    Get the new element with tag and text name as sub-element
    :param tag: tag name
    :param name: element name
    :return: etree.Element object
    """

    element = etree.Element(tag)
    etree.SubElement(element, NAME_TAG).text = name

    return element


def get_source_name(relpath: str, source: str) -> str:
    return os.path.join(IAR_PROJECT_DIR, relpath, source)


def path_to_xpath(path: str) -> list:
    os.path.split(path)
    return [group_xpath(item)
            for item in os.path.split(path)]


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
    # etree.indent(new_element)

    return new_element


if __name__ == '__main__':
    PATH_ID = "Path"
    PATTERN_ID = "Pattern"
    PROJECT_PATH_ID = "Project_dir"
    FIND_ALL_FILES = "*.*"

    parser = argparse.ArgumentParser(description="Make a list of files with "
                                                 "relative path")

    parser.add_argument(PATH_ID,
                        metavar='<path>',
                        type=str,
                        help='Path to source directory to add')

    parser.add_argument(PROJECT_PATH_ID,
                        metavar='<project_dir>',
                        type=str,
                        help='Project directory. Used as ' + IAR_PROJECT_DIR +
                             ' in the path to source.')

    parser.add_argument("-p",
                        "--pattern",
                        type=str,
                        help='Unix filename pattern matching',
                        default=FIND_ALL_FILES,
                        dest=PATTERN_ID)

    project_path = vars(parser.parse_args())[PROJECT_PATH_ID]
    project_dir, project_name = os.path.split(project_path)

    files = walk_through_files(
        project_dir,
        vars(parser.parse_args())[PATH_ID],
        vars(parser.parse_args())[PATTERN_ID])

    root = etree.parse(project_path)

    for f in files:
        groups, source = os.path.split(f)
        context = root
        for gr in groups.split('\\'):
            try:
                element = context.xpath(get_xpath(GROUP_TAG, gr))[0]
            except Exception:
                print(f"{gr} from {groups} not found. Adding it to the tree")
                element = append_child(context, GROUP_TAG, gr)

            context = element

        if not context.xpath(get_xpath(FILE_TAG, source)):
            append_child(
                context,
                FILE_TAG,
                get_source_name(groups, source))
            print("Added" + " " + f)

    etree.indent(root)
    with open(project_path, 'wb') as proj:
        proj.write(etree.tostring(root,
                                  encoding="iso-8859-1",
                                  pretty_print=True))
