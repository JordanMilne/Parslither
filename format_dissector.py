 
#base class for all dissectors

import construct


class FormatDissector(object):
    
    name = ""

    file_exts = [""]
    file_mimetype = [""]
    
    def dissect(self,  data):
        return construct.Container()
