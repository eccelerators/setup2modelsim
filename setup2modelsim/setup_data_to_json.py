#******************************************************************************
#
#                  /------o
#            eccelerators
#         o------/
#
# This file is an Eccelerators GmbH sample project.
#
# MIT License:
# Copyright (c) 2023 Eccelerators GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#******************************************************************************

from jinja2 import Environment, FileSystemLoader
from json import loads
from pathlib import Path


class SetupToJson:
    
    def extract(self, file_path='test/setup.py', write_json_file=False):
        file = open(file_path, 'r')
        lines = file.readlines()
        static_setup_data_lines_with_comments = []
        static_setup_data_lines = []
        in_static_setup_data_lines = False
        for l in lines: 
            if in_static_setup_data_lines : 
                static_setup_data_lines_with_comments.append(l)           
            if l.startswith("# start static_setup_data section"):
                in_static_setup_data_lines = True       
            if l.startswith("# end static_setup_data section"):
                in_static_setup_data_lines = False
        file.close()
        
        for l in static_setup_data_lines_with_comments: 
            if not l.strip().startswith('#'):
                l = l.replace('(', '[')
                l = l.replace(')', ']')
                static_setup_data_lines.append(l)
                
        static_setup_data_lines[0] = static_setup_data_lines[0].replace("static_setup_data = {", "{")
        
        s = ""
        for l in static_setup_data_lines: 
            s += l
        
        if write_json_file:
            f = open('static_setup_data.json', 'w')
            f.write(s)
            f.close()
        
        return s
    
if __name__ == '__main__':
    obj = SetupToJson()
    obj. extract(file_path='../../../setup.py', write_json_file=True)