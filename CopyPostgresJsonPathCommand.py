import sublime
import sublime_plugin
import json
from typing import Optional, List, Any, Union
from dataclasses import dataclass

@dataclass
class Position:
    """Represents a position range in the JSON text."""
    start: int
    end: int

    def contains(self, pos: int) -> bool:
        """Check if the given position is within this range."""
        return self.start <= pos <= self.end

class TreeNode:
    """Represents a node in the JSON tree structure."""
    def __init__(
        self,
        name: Union[str, int],
        position: Position,
        value: Optional[Any] = None
    ):
        self.name = name
        self.position = position
        self.value = value
        self.children: List['TreeNode'] = []

    def add_child(self, child: 'TreeNode') -> None:
        """Add a child node to this node."""
        self.children.append(child)

class JSONTreeParser:
    """Parser that converts JSON string to a tree structure with position information."""
    
    def __init__(self, json_str: str):
        self.json_str = json_str
        self.length = len(json_str)

    def parse(self) -> TreeNode:
        """Parse the JSON string into a tree structure."""
        try:
            data = json.loads(self.json_str)
            return self._build_tree('root', data, 0, self.length)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

    def _build_tree(
        self,
        name: Union[str, int],
        value: Any,
        start_pos: int,
        end_pos: int
    ) -> TreeNode:
        """Recursively build the tree structure."""
        node = TreeNode(name, Position(start_pos, end_pos))

        if isinstance(value, dict):
            self._build_dict_children(node, value, start_pos, end_pos)
        elif isinstance(value, list):
            self._build_list_children(node, value, start_pos, end_pos)
        else:
            node.value = value

        return node

    def _build_dict_children(
        self,
        node: TreeNode,
        value: dict,
        start_pos: int,
        end_pos: int
    ) -> None:
        """Build child nodes for dictionary values."""
        last_end_pos = start_pos
        for key, val in value.items():
            key_str = f'"{key}"'
            child_start = self.json_str.find(key_str, last_end_pos, end_pos)
            if child_start == -1:
                continue
            
            colon_pos = self.json_str.find(':', child_start, end_pos)
            if colon_pos == -1:
                continue
                
            value_start = self._find_value_start(colon_pos + 1, end_pos)
            value_end = self._find_value_end(value_start, end_pos)
            
            child = self._build_tree(key, val, value_start, value_end)
            node.add_child(child)
            last_end_pos = value_end

    def _build_list_children(
        self,
        node: TreeNode,
        value: list,
        start_pos: int,
        end_pos: int
    ) -> None:
        """Build child nodes for list values."""
        current_pos = start_pos
        for i, item in enumerate(value):
            item_start = self._find_value_start(current_pos, end_pos)
            item_end = self.json_str.find(
                ',', item_start, end_pos
            ) if i < len(value) - 1 else self.json_str.find(']', item_start, end_pos)
            
            if item_end == -1:
                item_end = end_pos
                
            child = self._build_tree(i, item, item_start, item_end)
            node.add_child(child)
            current_pos = item_end + 1

    def _find_value_start(self, start: int, end: int) -> int:
        """Find the start position of a value, skipping whitespace."""
        for i in range(start, end):
            if not self.json_str[i].isspace():
                return i
        return start

    def _find_value_end(self, start: int, end: int) -> int:
        """Find the end position of a value."""
        stack = []
        in_string = False
        
        for i in range(start, end):
            char = self.json_str[i]
            
            # Handle string literals
            if char == '"' and (i == 0 or self.json_str[i-1] != '\\'):
                in_string = not in_string
                continue
                
            if not in_string:
                if char in '{[':
                    stack.append(char)
                elif char in '}]':
                    if stack:
                        stack.pop()
                    if not stack:
                        return i + 1
                elif char == ',' and not stack:
                    return i
                    
        return end

class JSONPathFinder:
    """Utility for finding JSON paths based on cursor position."""
    
    @staticmethod
    def find_path(node: TreeNode, position: int) -> List[Union[str, int]]:
        """Find the path to the node containing the position."""
        path: List[Union[str, int]] = []
        
        def traverse(current: TreeNode) -> None:
            if current.position.contains(position):
                path.append(current.name)
                for child in current.children:
                    traverse(child)
                    
        traverse(node)
        return path[1:] if path else []  # Remove root node

    @staticmethod
    def find_value(node: TreeNode, position: int) -> Optional[Any]:
        """Find the value at the given position."""
        value = None
        
        def traverse(current: TreeNode) -> None:
            nonlocal value
            if current.position.contains(position):
                value = current.value
                for child in current.children:
                    traverse(child)
                    
        traverse(node)
        return value

class PathFormatter:
    """Formats JSON paths for PostgreSQL style output."""
    
    @staticmethod
    def format_item(item: Union[str, int]) -> str:
        """Format a single path item."""
        return str(item) if isinstance(item, int) else f"'{item}'"

    @staticmethod
    def format_path(path: List[Union[str, int]], value: Any) -> str:
        """Format the complete path with value."""
        if not path:
            return ''
            
        if len(path) == 1:
            path_str = f'->>{PathFormatter.format_item(path[0])}'
        else:
            path_items = [PathFormatter.format_item(item) for item in path[:-1]]
            path_str = '->' + '->'.join(path_items) + '->>' + PathFormatter.format_item(path[-1])
            
        return f"{path_str} = '{value}'"

class CopyPostgresJsonPathCommand(sublime_plugin.TextCommand):
    """Sublime Text command to copy PostgreSQL JSON path."""
    
    def run(self, edit: sublime.Edit) -> None:
        try:
            view = self.view
            sel = view.sel()[0]
            content = view.substr(sublime.Region(0, view.size()))
            cursor_pos = sel.begin()
            
            # Parse JSON and find path
            tree = JSONTreeParser(content).parse()
            path = JSONPathFinder.find_path(tree, cursor_pos)
            
            if not path:
                sublime.status_message("No JSON path found")
                return
                
            # Get value and format path
            value = JSONPathFinder.find_value(tree, cursor_pos)
            formatted_path = PathFormatter.format_path(path, value)
            
            # Copy to clipboard
            sublime.set_clipboard(formatted_path)
            sublime.message_dialog(f"JSON path copied to clipboard: {formatted_path}")
            
        except Exception as e:
            sublime.error_message(f"Error: {str(e)}")