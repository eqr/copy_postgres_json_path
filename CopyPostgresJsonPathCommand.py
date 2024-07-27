import sublime
import sublime_plugin
import json

class CopyPostgresJsonPathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get the cursor position
        cursor_position = self.view.sel()[0].begin()
        
        # Get the word at the cursor position
        word_region = self.view.word(cursor_position)
        word_at_cursor = self.view.substr(word_region)

        
        # Get the entire content of the file
        file_content = self.view.substr(sublime.Region(0, self.view.size()))

        try:
            # Parse the JSON content
            json_content = json.loads(file_content)
        except json.JSONDecodeError:
            sublime.error_message("Invalid JSON content")
            return

        # Find the path to the element at the cursor position
        path = self.find_path(json_content, word_at_cursor, [])


        if path:
            # Construct the result string with the last arrow as ->>
            if len(path) > 1:
                # Debugging: Print the types of segments in the path
                for segment in path[:-1]:
                    print(f"Segment: {segment}, Type: {type(segment)}")
                result = "->" + "->".join([self.format_segment(segment) for segment in path[:-1]]) + "->>" + self.format_segment(path[-1])
            else:
                result = "->>" + self.format_segment(path[0])
            sublime.message_dialog("Path to the element at cursor: " + result)
            sublime.set_clipboard(result)
        else:
            sublime.message_dialog("Element not found in JSON")

    def find_path(self, json_content, word_at_cursor, path_segments):
        if isinstance(json_content, dict):
            for key, value in json_content.items():
                new_path_segments = path_segments + [key]
                if key == word_at_cursor or str(value) == word_at_cursor:
                    return new_path_segments
                result = self.find_path(value, word_at_cursor, new_path_segments)
                if result:
                    return result
        elif isinstance(json_content, list):
            for index, item in enumerate(json_content):
                new_path_segments = path_segments + [index]
                if str(item) == word_at_cursor:
                    return new_path_segments
                result = self.find_path(item, word_at_cursor, new_path_segments)
                if result:
                    return result
        return None

    def format_segment(self, segment):
        return str(segment) if isinstance(segment, int) else f"'{segment}'"