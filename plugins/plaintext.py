
from format_dissector import FormatDissector

class PlaintextDissector(FormatDissector):
    
    name = "Plain Text"

    file_exts = [".txt"]
    file_mimetypes = ["text/plain"]
    
    def dissect(self,  data):
        return data
