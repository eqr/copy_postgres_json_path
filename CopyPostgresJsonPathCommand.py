import sublime
import sublime_plugin
import json

class TreeNode:
    def __init__(self, name, value=None, start_pos=None, end_pos=None):
        self.name = name
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.children = []

    def add_child(self, child):
        self.children.append(child)

def parse_json_to_tree(json_str):
    def build_tree(name, value, start_pos, end_pos):
        node = TreeNode(name, start_pos=start_pos, end_pos=end_pos)
        if isinstance(value, dict):
            last_end_pos = start_pos
            for k, v in value.items():
                key_str = f'"{k}"'
                child_start_pos = json_str.find(key_str, last_end_pos, end_pos)
                child_start_pos = json_str.find(':', child_start_pos) + 1
                child_start_pos = find_value_start(json_str, child_start_pos, end_pos)
                child_end_pos = find_value_end(json_str, child_start_pos, end_pos)
                child = build_tree(k, v, child_start_pos, child_end_pos)
                node.add_child(child)
                last_end_pos = child_end_pos
        elif isinstance(value, list):
            current_pos = start_pos
            for i, item in enumerate(value):
                item_start_pos = find_value_start(json_str, current_pos, end_pos)
                if i < len(value) - 1:
                    item_end_pos = json_str.find(',', item_start_pos, end_pos)
                else:
                    item_end_pos = json_str.find(']', item_start_pos, end_pos)
                child = build_tree(f'{i}', item, item_start_pos, item_end_pos)
                node.add_child(child)
                current_pos = item_end_pos + 1
        else:
            node.value = value
        return node

    def find_value_start(json_str, start_pos, end_pos):
        for i in range(start_pos, end_pos):
            if not json_str[i].isspace():
                return i
        return start_pos

    def find_value_end(json_str, start_pos, end_pos):
        stack = []
        in_string = False
        for i in range(start_pos, end_pos):
            if json_str[i] == '"' and (i == 0 or json_str[i-1] != '\\'):
                in_string = not in_string
            if not in_string:
                if json_str[i] in '{[':
                    stack.append(json_str[i])
                elif json_str[i] in '}]':
                    if stack:
                        stack.pop()
                    if not stack:
                        return i + 1
                elif json_str[i] == ',' and not stack:
                    return i
        return end_pos

    data = json.loads(json_str)
    root = build_tree('root', data, 0, len(json_str))
    return root

def print_tree(node, level=0):
    indent = ' ' * (level * 4)
    if node.value is not None:
        print(f"{indent}{node.name}: {node.value} (start: {node.start_pos}, end: {node.end_pos})")
    else:
        print(f"{indent}{node.name} (start: {node.start_pos}, end: {node.end_pos})")
    for child in node.children:
        print_tree(child, level + 1)

def find_path_by_position(node, position):
    path = []

    def traverse(node, position):
        if node.start_pos <= position <= node.end_pos:
            path.append(node.name)
            for child in node.children:
                traverse(child, position)

    traverse(node, position)
    return path

def find_value_by_position(node, position):
    value = None

    def traverse(node, position):
        nonlocal value
        if node.start_pos <= position <= node.end_pos:
            value = node.value
            for child in node.children:
                traverse(child, position)

    traverse(node, position)
    return value

def format_item(item):
    if isinstance(item, int):
        return f'{item}'
    return f'\'{item}\''

def format_path(path, val):
    if len(path) == 0:
        return ''
    if len(path) == 1:
        p = (f'->>{format_item(path[0])}')
    else: 
        p = '->' + '->'.join([format_item(item) for item in path[:-1]]) + '->>' + format_item(path[-1])

    return p + f' = \'{val}\''

class CopyPostgresJsonPathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()[0]
        file_content = view.substr(sublime.Region(0, view.size()))
        cursor_position = sel.begin()
        tree = parse_json_to_tree(file_content)
        path = find_path_by_position(tree,cursor_position)

        if not path:
            sublime.status_message("No JSON path found")
            return
        path = path[1:] # remove root node
        val = find_value_by_position(tree, cursor_position)

        formatted_path = format_path(path, val)        
        sublime.message_dialog(f"JSON path copied to clipboard: {formatted_path}")
        sublime.set_clipboard(formatted_path)
import sublime
import sublime_plugin
import json

class TreeNode:
    def __init__(self, name, value=None, start_pos=None, end_pos=None):
        self.name = name
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.children = []

    def add_child(self, child):
        self.children.append(child)

def parse_json_to_tree(json_str):
    def build_tree(name, value, start_pos, end_pos):
        node = TreeNode(name, start_pos=start_pos, end_pos=end_pos)
        if isinstance(value, dict):
            last_end_pos = start_pos
            for k, v in value.items():
                key_str = f'"{k}"'
                child_start_pos = json_str.find(key_str, last_end_pos, end_pos)
                child_start_pos = json_str.find(':', child_start_pos) + 1
                child_start_pos = find_value_start(json_str, child_start_pos, end_pos)
                child_end_pos = find_value_end(json_str, child_start_pos, end_pos)
                child = build_tree(k, v, child_start_pos, child_end_pos)
                node.add_child(child)
                last_end_pos = child_end_pos
        elif isinstance(value, list):
            current_pos = start_pos
            for i, item in enumerate(value):
                item_start_pos = find_value_start(json_str, current_pos, end_pos)
                if i < len(value) - 1:
                    item_end_pos = json_str.find(',', item_start_pos, end_pos)
                else:
                    item_end_pos = json_str.find(']', item_start_pos, end_pos)
                child = build_tree(i, item, item_start_pos, item_end_pos)
                node.add_child(child)
                current_pos = item_end_pos + 1
        else:
            node.value = value
        return node

    def find_value_start(json_str, start_pos, end_pos):
        for i in range(start_pos, end_pos):
            if not json_str[i].isspace():
                return i
        return start_pos

    def find_value_end(json_str, start_pos, end_pos):
        stack = []
        in_string = False
        for i in range(start_pos, end_pos):
            if json_str[i] == '"' and (i == 0 or json_str[i-1] != '\\'):
                in_string = not in_string
            if not in_string:
                if json_str[i] in '{[':
                    stack.append(json_str[i])
                elif json_str[i] in '}]':
                    if stack:
                        stack.pop()
                    if not stack:
                        return i + 1
                elif json_str[i] == ',' and not stack:
                    return i
        return end_pos

    data = json.loads(json_str)
    root = build_tree('root', data, 0, len(json_str))
    return root

def print_tree(node, level=0):
    indent = ' ' * (level * 4)
    if node.value is not None:
        print(f"{indent}{node.name}: {node.value} (start: {node.start_pos}, end: {node.end_pos})")
    else:
        print(f"{indent}{node.name} (start: {node.start_pos}, end: {node.end_pos})")
    for child in node.children:
        print_tree(child, level + 1)

def find_path_by_position(node, position):
    path = []

    def traverse(node, position):
        if node.start_pos <= position <= node.end_pos:
            path.append(node.name)
            for child in node.children:
                traverse(child, position)

    traverse(node, position)
    return path

def find_value_by_position(node, position):
    value = None

    def traverse(node, position):
        nonlocal value
        if node.start_pos <= position <= node.end_pos:
            value = node.value
            for child in node.children:
                traverse(child, position)

    traverse(node, position)
    return value

def format_item(item):
    print(item, isinstance(item, int))
    if isinstance(item, int):
        return f'{item}'
    return f'\'{item}\''

def format_path(path, val):
    if len(path) == 0:
        return ''
    if len(path) == 1:
        p = (f'->>{format_item(path[0])}')
    else: 
        p = '->' + '->'.join([format_item(item) for item in path[:-1]]) + '->>' + format_item(path[-1])

    return p + f' = \'{val}\''

class CopyPostgresJsonPathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()[0]
        file_content = view.substr(sublime.Region(0, view.size()))
        cursor_position = sel.begin()
        tree = parse_json_to_tree(file_content)
        path = find_path_by_position(tree,cursor_position)

        if not path:
            sublime.status_message("No JSON path found")
            return
        path = path[1:] # remove root node
        val = find_value_by_position(tree, cursor_position)

        formatted_path = format_path(path, val)        
        sublime.message_dialog(f"JSON path copied to clipboard: {formatted_path}")
        sublime.set_clipboard(formatted_path)
