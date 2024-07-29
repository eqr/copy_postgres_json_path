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
                child = build_tree(f'[{i}]', item, item_start_pos, item_end_pos)
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

if __name__ == '__main__':
    json_str = '''{
  "a": "b",
  "c": {
    "d": {
      "e": ["f", "o", {"g": "j"}, "t"],
      "o": "p"
    }
  }
}
'''
    
    print(json_str)
    
    tree = parse_json_to_tree(json_str)
    print_tree(tree)
    
    # Adjust the position to point to the actual value, not the quote
    position = json_str.find('"t"') + 1  # Example position for "p"
    print(position)
    path = find_path_by_position(tree, position)
    print("Path to element at position", position, ":", " -> ".join(path))
