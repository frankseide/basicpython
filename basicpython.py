#!/usr/bin/python3

import code
import os
#import readline
import prompt_toolkit
import rlcompleter
from collections import OrderedDict
import re

# SomeClass will be available in the interactive console
#from yourmodule import SomeClass

class BasicPython(object):
    def __init__():
        pass

session = prompt_toolkit.PromptSession()
readline = prompt_toolkit.prompt
vars = globals()
vars.update(locals())
#readline.set_completer(rlcompleter.Completer(vars).complete)
#readline.parse_and_bind("tab: complete")
shell = code.InteractiveInterpreter(vars)
import psutil
mem = psutil.virtual_memory().total
banner = "\n    **** BASIC PYTHON V1 ****\n\n{:,} OF BYTES FREE\n".format(mem)
print(banner)
program = OrderedDict()

def run_program():
    program_lines = [l for (n,l) in program.items()]
    obj = compile('\n'.join(program_lines), 'program', mode='exec')
    exec(obj, globals(), locals())

def is_edit_command(line):
    if line == "list":
        for l in program.items():
            print("{:5d}".format(l[0]), l[1])
        return True
    if line == "run":
        run_program()
        return True
    return False

def is_add_command(line):
    #del_line_pattern = re.compile('^del +([0-9]+) *$')
    add_line_pattern = re.compile('^ *([0-9]+) (.*)$')
    m = add_line_pattern.match(line)
    if not m:
        return False
    g = m.groups()
    line_no = int(g[0])
    code = g[1]
    program[line_no] = code
    #print('line_no=', line_no, 'code=', code)
    return True 

while True:
    print("READY.")
    line = session.prompt()
    while is_add_command(line):
        line = session.prompt()
        # TODO: keep prompt after list
        pass
    if is_edit_command(line):
        continue
    while shell.runsource(line):
        line = line + '\n' + session.prompt()
