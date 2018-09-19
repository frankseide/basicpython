#!/usr/bin/python3

import code
import os
import sys
import traceback
#import readline
import prompt_toolkit
from prompt_toolkit.filters import HasSelection, Condition
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.history import InMemoryHistory
#from prompt_toolkit import print_formatted_text
import rlcompleter
from collections import OrderedDict
import re
import pygments
from pygments.lexers import Python3Lexer
from prompt_toolkit.layout.lexers import PygmentsLexer

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
program_path = None

pyglexer = Python3Lexer()
lexer = PygmentsLexer(Python3Lexer)

def program_items(): # use this to read out program, items() won't sort
    sorted_line_nos = sorted(program.keys())
    return [(n, program[n]) for n in sorted_line_nos] # TODO: do this right

def run_program():
    program_lines = [l for (n,l) in program_items()]
    obj = compile('\n'.join(program_lines), 'program', mode='exec')
    exec(obj, globals(), locals())

def handle_exception(e):
    print("".join(traceback.format_exception(*sys.exc_info())))

def is_edit_command(line) -> bool: # -> bool
    global program
    global program_path
    p = re.compile('^([a-z]+) +(.*)$')
    p1 = re.compile('^([a-z]+) *$')
    m  = p.match(line)
    m1 = p1.match(line)
    if m1:
        cmd = m1.groups()[0]
        arg = None
    elif m:
        cmd, arg = m.groups()
    else:
       return False
    def handled_with_err(msg):
        print(msg)
        return True
    def unexpected_arg():
        return handled_with_err('SyntaxError: unexpected argument was given.')
    def arg_expected():
        return handled_with_err('SyntaxError: required argument missing')
    if cmd == "new":
        if arg is not None:
            return unexpected_arg()
        program = OrderedDict()
        program_path = None
        return True
    elif cmd == "renumber":
        if arg is not None:
            return unexpected_arg()
        items = program_items()
        program = OrderedDict()
        no = 10
        for item in items:
            program[no] = item[1]
            no += 10
        return True
    elif line == "list":
        if len(program_items()) == 0:
            return True # empty program
        program_text = '\n'.join(line for no, line in program_items())+'\n'
        lexed = pygments.lex(program_text, pyglexer)
        def print_formatted_text(toks):
            print(''.join(s for _, s in toks), end='')
        nos = [no for no, line in program_items()]
        i = 0
        line = []
        for item in lexed:
            if len(line) == 0:
                line += [('Python3Lexer.Token.Literal.Number.Integer', "{:5} ".format(nos[i]))]
                i = i+1
            line += [item]
            if item[1] == '\n':
                print_formatted_text(line)
                line = []
        return True
    elif cmd == "run":
        if arg is None:
            try:
                run_program()
            except Exception as e:
                handle_exception(e)
                pass
            except KeyboardInterrupt:
                print('Ctrl-C')
                pass
            return True
        else: # run PATH
            is_edit_command("load " + line[4:])
            return is_edit_command("run")
    elif cmd == "save":
        if arg is None:
            if program_path is None:
                return arg_expected()
            arg = program_path # default to last used pathname
        path = arg + ".pyl"
        with open(path, 'w') as f:
            f.writelines("{:5} {}\n".format(*items)
                         for items in program_items())
        print('Saved {} lines to'.format(len(program_items())), path)
        program_path = arg
        return True
    elif cmd == "load":
        if arg is None:
            return arg_expected()
        path = arg + ".pyl"
        with open(path, 'r') as f:
            program = OrderedDict((int(line[:6]), line[6:-1])
                                  for line in f.readlines())
        print('Loaded {} lines from'.format(len(program_items())), path)
        program_path = arg
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

bindings = load_key_bindings(enable_search=True, enable_auto_suggest_bindings=True)
handle = bindings.add_binding

@handle(' ')
def _(event):
    p = re.compile('^( *)([0-9]+)$')
    b = event.current_buffer
    m = p.match(b.text)
    if m: # TODO: check if we are at line end --  space after line number
        g = m.groups()
        spaces_needed = 5 - len(g[0]) - len(g[1])
        if spaces_needed > 0:
            b.delete_before_cursor(len(g[1]))
            b.insert_text(' ' * spaces_needed + g[1], overwrite=True)
        b.insert_text(' ') # insert the actual space
        # if line exists then bring it into the editr
        no = int(g[1])
        if no in program:
            b.insert_text(program[no], move_cursor=False)
    else:
        b.insert_text(' ') # regular space
@handle(Keys.ControlC)
def _(event):
    event.cli.abort()
# from basic.py:
suggestion_available = Condition(
    lambda cli:
        cli.current_buffer.suggestion is not None and
        cli.current_buffer.document.is_cursor_at_the_end)

@handle(Keys.ControlF, filter=suggestion_available)
@handle(Keys.ControlE, filter=suggestion_available)
@handle(Keys.Right, filter=suggestion_available)
def _(event):
    " Accept suggestion. "
    b = event.current_buffer
    suggestion = b.suggestion

    if suggestion:
        b.insert_text(suggestion.text)

last_edited_line = None

#session = prompt_toolkit.PromptSession(key_bindings=bindings)
history = InMemoryHistory()

def getline(last_edited_line):
    prefix = ""
    suffix = ""
    if last_edited_line is not None:
        next_line = last_edited_line + 10 # TODO: check next existing line
        prefix = "{:5} ".format(next_line)
        if next_line in program:
            suffix = program[next_line]
    try:    
        return prompt_toolkit.prompt(key_bindings_registry=bindings,
            default=prefix + suffix,
            history=history,
            lexer=lexer) # TODO: cursor at pfx
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
