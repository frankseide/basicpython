#!/usr/bin/python3

import code
import os
import sys
import traceback
#import readline
import prompt_toolkit
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings
from prompt_toolkit.keys import Keys
import rlcompleter
from collections import OrderedDict
import re

# SomeClass will be available in the interactive console
#from yourmodule import SomeClass

class BasicPython(object):
    def __init__():
        pass

vars = globals()
vars.update(locals())
#readline.set_completer(rlcompleter.Completer(vars).complete)
#readline.parse_and_bind("tab: complete")
shell = code.InteractiveInterpreter(vars)
import psutil
mem = psutil.virtual_memory().total
banner = "\n    **** BASIC PYTHON V1 ****\n\n{:,} BYTES FREE\n".format(mem)
print(banner)
program = OrderedDict()

def program_items(): # use this to read out program, items() won't sort
    sorted_line_nos = sorted(program.keys())
    return [(n, program[n]) for n in sorted_line_nos] # TODO: do this right

def run_program():
    program_lines = [l for (n,l) in program_items()]
    obj = compile('\n'.join(program_lines), 'program', mode='exec')
    exec(obj, globals(), locals())

def handle_exception(e):
    print("".join(traceback.format_exception(*sys.exc_info())))

def is_edit_command(line):
    global program
    if line == "new":
        program = OrderedDict()
        return True
    if line == "renumber":
        items = program_items()
        program = OrderedDict()
        no = 10
        for item in items:
            program[no] = item[1]
            no += 10
        return True
    if line == "list":
        for l in program_items():
            print("{:5d}".format(l[0]), l[1])
        return True
    if line == "run":
        try:
            run_program()
        except Exception as e:
            handle_exception(e)
            pass
        except KeyboardInterrupt:
            print('Ctrl-C')
            pass
        return True
    if line.startswith("run "):
        is_edit_command("load " + line[4:])
        return is_edit_command("run")
    if line.startswith("save "):
        path = line[5:] + ".pyl"
        with open(path, 'w') as f:
            f.writelines("{:5} {}\n".format(*items)
                         for items in program_items())
        print('saved {} lines to'.format(len(program_items())), path)
        return True
    if line.startswith("load "):
        path = line[5:] + ".pyl"
        with open(path, 'r') as f:
            program = OrderedDict((int(line[:6]), line[6:-1])
                                  for line in f.readlines())
        print('loaded {} lines from'.format(len(program_items())), path)
        return True
    return False

def is_add_command(line):
    #del_line_pattern = re.compile('^del +([0-9]+) *$')
    add_line_pattern = re.compile('^ *([0-9]+) (.*)$')
    m = add_line_pattern.match(line)
    if not m:
        return (None, line)
    g = m.groups()
    line_no = int(g[0])
    code = g[1]
    if code == "": # user just hit enter
        return (None, "")
    program[line_no] = code
    #print('line_no=', line_no, 'code=', code)
    return (line_no, line)

bindings = load_basic_bindings()
handle = bindings.add_binding

@handle(' ')
def _(event):
    p = re.compile('^( *)([0-9]+)$')
    buf = event.current_buffer
    m = p.match(buf.text)
    if m: # TODO: check if we are at line end --  space after line number
        g = m.groups()
        spaces_needed = 5 - len(g[0]) - len(g[1])
        if spaces_needed > 0:
            buf.delete_before_cursor(len(g[1]))
            buf.insert_text(' ' * spaces_needed + g[1], overwrite=True)
        buf.insert_text(' ') # insert the actual space
        # if line exists then bring it into the editr
        no = int(g[1])
        if no in program:
            buf.insert_text(program[no], move_cursor=False)
    else:
        buf.insert_text(' ') # regular space
@handle(Keys.ControlC)
def _(event):
    event.cli.abort()

last_edited_line = None

#session = prompt_toolkit.PromptSession(key_bindings=bindings)

def getline(last_edited_line):
    prefix = ""
    suffix = ""
    if last_edited_line is not None:
        next_line = last_edited_line + 10 # TODO: check next existing line
        prefix = "{:5} ".format(next_line)
        if next_line in program:
            suffix = program[next_line]
    try:    
        return prompt_toolkit.prompt(key_bindings_registry=bindings, default=prefix + suffix) # TODO: cursor at pfx
    except KeyboardInterrupt:
        return ""
 
while True:
    print("READY.")
    line = getline(last_edited_line)
    (last_edited_line, line) = is_add_command(line)
    while last_edited_line is not None:
        line = getline(last_edited_line)
        (last_edited_line, line) = is_add_command(line)
        # TODO: keep prompt after list
        pass
    if is_edit_command(line):
        continue
    try:
        while shell.runsource(line):
            line = line + '\n' + getline(None)
    except Exception as e:
        handle_exception(e)
        pass
