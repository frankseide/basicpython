#!/usr/bin/python3

import code
import os
import sys
import traceback
import prompt_toolkit
from prompt_toolkit.filters import HasSelection, Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import PygmentsTokens
import rlcompleter
from collections import OrderedDict
import re
import pygments
from pygments.lexers import Python3Lexer
from pygments.token import Token
from prompt_toolkit.lexers import PygmentsLexer

vars = globals()
vars.update(locals())
shell = code.InteractiveInterpreter(vars)
import psutil
mem = psutil.virtual_memory().total
banner = "\n    **** BASIC PYTHON V1 ****\n\n{:,} BYTES FREE\n".format(mem)
print(banner)

program = OrderedDict()
program_path = None
program_hash_bang = None

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

# TODO: in case of error, we should throw, and catch this above
def is_edit_command(line) -> bool: # -> bool
    global program
    global program_path
    global program_hash_bang
    p = re.compile('^([a-z]+)( ?) *(.*)$')
    p1 = re.compile('^([a-z]+) *$')
    m  = p.match(line)
    m1 = p1.match(line)
    if not m:
        return False
    cmd, space, arg = m.groups()
    if space == '' and arg != '':
        return False # e.g. 'save13 = 5'
    if arg == '':
        arg = None
    def handled_with_err(msg):
        print(msg)
        return True
    def unexpected_arg():
        return handled_with_err('SyntaxError: unexpected argument')
    def arg_expected():
        return handled_with_err('SyntaxError: required argument missing')
    def parse_no_range(arg): # None if malformed (error already printed)
        if arg is None:
            arg = ''
        p = re.compile('^([0-9]*)(-?)([0-9]*)$')
        m = p.match(arg)
        def malformed():
            handled_with_err("SyntaxError: mal-formed line number range")
            return None
        if not m:
            return malformed()
        first, dash, last = m.groups()
        first = int(first) if first != '' else None
        last  = int(last)  if last  != '' else first if dash != '-' else None
        if first is not None and last is not None and first > last:
            return malformed()
        if ((first is not None and first not in program) or
            (last  is not None and last  not in program)):
            handled_with_err("SyntaxError: no such line number")
            return None
        return (first, last)
    def in_no_range(no, r):
        first_no, last_no = r
        return ((first_no is None or no >= first_no) and
                (last_no  is None or no <= last_no))
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
    elif cmd == "del" and arg and re.compile('^[0-9-]').match(arg):
        r = parse_no_range(arg)
        if not r:
            return True # invalid, and error already printed
        del_nos = (no for no, _ in program_items() if in_no_range(no, r))
        for no in del_nos:
            del program[no]
        return True
    elif cmd == "list" and (not arg or re.compile('^[0-9-]').match(arg)):
        r = parse_no_range(arg)
        if not r:
            return True # invalid, and error already printed
        if len(program_items()) == 0:
            return True # empty program
        def next_line(items):        
            program_text = '\n'.join(line for no, line in items) + '\n'
            lexed = pygments.lex(program_text, pyglexer)
            no_iter = iter([no for no, line in items]) # line numbers
            line = []
            for item in lexed:
                if item[1] == '\n': # end of line: yield it
                    no = next(no_iter) # this is its line number
                    yield (no, line)
                    line = []
                else:
                    line.append(item)
        shown = False
        for no, lex_tuples in next_line(program_items()):
            if not in_no_range(no, r):
                if shown:
                    break
                else:
                    continue
            no_tuple = (Token.Literal.Number.Integer, "{:5} ".format(no))
            print_formatted_text(PygmentsTokens([no_tuple] + lex_tuples))
            shown = True
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
        path = arg + ".py"
        hb = program_hash_bang or "#!/usr/bin/python3"
        # where line numbers do not follow the 10-increment pattern,
        # we add a line-no comment to set the line number
        def lines(items):
            yield hb # make files self-executable
            expected_no = 10
            for item in program_items():
                no, line = item
                if no != expected_no:
                    yield "# line-no: " + str(no)
                yield line
                expected_no = no + 10
        with open(path, 'w') as f:
            f.writelines(line + '\n'
                         for line in lines(program_items()))
        os.chmod(path, 0o777)
        print('Saved {} lines to'.format(len(program_items())), path)
        program_path = arg
        program_hash_bang = hb
        return True
    elif cmd == "load":
        if arg is None:
            return arg_expected()
        path = arg + ".py"
        with open(path, 'r') as f:
            lines = f.readlines()
        line_tuples = []
        no = 10
        hb = None
        for line in lines:
            if not line_tuples and line.startswith("#!"):
                hb = line[:-1]
            elif line.startswith("# line-no: "):
                no = int(line[11:])
            else:
                line_tuples += [(no, line[:-1])]
                no += 10
        program = OrderedDict(line_tuples)
        print('Loaded {} lines from'.format(len(program_items())), path)
        program_path = arg
        program_hash_bang = hb
        return True
    return False

def is_add_command(line):
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

bindings = KeyBindings() #load_key_bindings(enable_search=True, enable_auto_suggest_bindings=True)
handle = bindings.add

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

last_edited_line = None

history = InMemoryHistory()
session = prompt_toolkit.PromptSession(key_bindings=bindings,
                                       history=history,
                                       lexer=lexer)

def getline(last_edited_line):
    prefix = ""
    suffix = ""
    if last_edited_line is not None:
        next_line = last_edited_line + 10 # TODO: check next existing line
        prefix = "{:5} ".format(next_line)
        if next_line in program:
            suffix = program[next_line]
    try:
        return session.prompt(default=prefix + suffix) # TODO: cursor at pfx
        #return prompt_toolkit.prompt(default=prefix + suffix,key_bindings=bindings,
        #                               lexer=lexer) # TODO: cursor at pfx
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
