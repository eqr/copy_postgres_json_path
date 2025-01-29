import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Mock sublime and sublime_plugin modules
sys.modules['sublime'] = MagicMock()
sys.modules['sublime_plugin'] = MagicMock()

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our module
from CopyPostgresJsonPathCommand import JSONTreeParser, JSONPathFinder, PathFormatter

class CopyPostgresJsonPathTest(unittest.TestCase):
    def setUp(self):
        self.sample_json = '''{
            "name": "John",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "Boston"
            },
            "phones": [
                {"type": "home", "number": "555-1234"},
                {"type": "work", "number": "555-5678"}
            ]
        }'''

    def test_parser(self):
        parser = JSONTreeParser(self.sample_json)
        tree = parser.parse()
        self.assertEqual(tree.name, "root")
        self.assertEqual(len(tree.children), 4)  # name, age, address, phones

    def test_path_finder(self):
        tree = JSONTreeParser(self.sample_json).parse()
        # Find position of "John"
        pos = self.sample_json.find('"John"')
        path = JSONPathFinder.find_path(tree, pos)
        self.assertEqual(path, ["name"])
        
        # Find nested value
        pos = self.sample_json.find('"Boston"')
        path = JSONPathFinder.find_path(tree, pos)
        self.assertEqual(path, ["address", "city"])

    def test_path_formatter(self):
        path = ["address", "city"]
        formatted = PathFormatter.format_path(path, "Boston")
        self.assertEqual(formatted, "->'address'->>'city' = 'Boston'")

    def test_value_finder(self):
        tree = JSONTreeParser(self.sample_json).parse()
        pos = self.sample_json.find('"Boston"')
        value = JSONPathFinder.find_value(tree, pos)
        self.assertEqual(value, "Boston")

    def test_invalid_json(self):
        invalid_json = '{invalid"}'
        with self.assertRaises(ValueError):
            JSONTreeParser(invalid_json).parse()
            
    def test_nested_list_path(self):
        json_str = '''{
            "items": [
                {"id": 1, "name": "first"},
                {"id": 2, "name": "second"}
            ]
        }'''
        tree = JSONTreeParser(json_str).parse()
        pos = json_str.find('"second"')
        path = JSONPathFinder.find_path(tree, pos)
        self.assertEqual(path, ["items", 1, "name"])
        
    def test_empty_path(self):
        tree = JSONTreeParser(self.sample_json).parse()
        path = JSONPathFinder.find_path(tree, 999999)  # Position outside of JSON
        self.assertEqual(path, [])
        
    def test_array_index_formatting(self):
        path = ["items", 1, "name"]
        formatted = PathFormatter.format_path(path, "second")
        self.assertEqual(formatted, "->'items'->1->>'name' = 'second'")

if __name__ == '__main__':
    unittest.main()