from backend.repository.tools import count_tokens

class TokenTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.tool_calls = 0
        self.files_read = 0

    def add_input(self, text: str):
        self.input_tokens += count_tokens(text)

    def add_output(self, text: str):
        self.output_tokens += count_tokens(text)
        
    def add_file_read(self):
        self.files_read += 1
        
    def get_metrics(self) -> dict:
        return {
            "total_tokens": self.input_tokens + self.output_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "files_read": self.files_read
        }
