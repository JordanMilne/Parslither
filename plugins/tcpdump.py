

from format_dissector import FormatDissector
from construct.formats.data.cap import cap_file
from construct import *


class TCPDumpDissector(FormatDissector):
    
    name = "TCPDump capture"

    file_exts = [".cap", ".pcap", ".tcpdump"]
    file_mimetypes = ["application/vnd.tcpdump.pcap"]
    
    def dissect(self,  data):
        return cap_file.parse(data)
