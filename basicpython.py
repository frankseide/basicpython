#!/usr/bin/python3

import os
import sys

# we capture the globals before importing our stuff
vars = dict(globals())
vars.update(locals())

import code
import traceback
import prompt_toolkit
from prompt_toolkit.filters import HasSelection, Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import PygmentsTokens
import rlcompleter
import re
import pygments
from pygments.lexers import Python3Lexer
from pygments.token import Token
from prompt_toolkit.lexers import PygmentsLexer

class TheProgram:
    pyglexer = Python3Lexer()

    def __init__(self, path=None, hash_bang=None):
        self._program = dict()
        self.path = path
        self.hash_bang = hash_bang

    def in_no_range(no, range): # test if line number is within a given optional range tuple
        if not range: # no range constraint given
            return True
        first_no, last_no = range
        return ((first_no is None or no >= first_no) and
                (last_no  is None or no <= last_no))

    def line_nos(self, range=None): # generator that returns our lines, optionally within a given range
        # TODO: cache this
        # TODO: create a proper iterator that iterates this object in line order
        nos = list(self._program.keys()) # Python has no equivalent of an ordered map
        nos.sort()
        any = False
        for no in nos:
            if not TheProgram.in_no_range(no, range):
                if any:
                    break
                else:
                    continue
            yield no
            any = True

    def text(self):
        return (self._program[no] for no in self.line_nos())

    def add(self, no, line):
        self._program[no] = line

    def erase(self, no):
        # TODO: just use the __ routine directly to allow 'del' on this objects
        del self._program[no]

    def get(self, no):
        return self._program[no]

    def try_get(self, no):
        try:
            return get(no)
        except:
            return None

    def get_lexed(self, no):
        # TODO: lex the whole thing, not just line by line
        # TODO: cache this
        return pygments.lex(self._program[no], TheProgram.pyglexer)

    def next_line_no_after(self, line_no):
        nos = list(self.line_nos())
        i = 1 + nos.index(line_no)
        # TODO: there probably is a proper iterator-based way to do this
        if i < len(nos):
            return min(line_no + 10, nos[i])
        else:
            return line_no + 10

    def renumbered(self):
        new_program = TheProgram(path=self.path, hash_bang=self.hash_bang)
        new_no = 10
        for item in iter(self):
            new_program.add(new_no, item[1])
            new_nono += 10
        return new_program

    def load(path):
        new_program = TheProgram(path=path)
        no = 10
        first = True
        for line in open(path, 'r').readlines():
            if first and line.startswith("#!"):
                new_program.hash_bang = line[:-1]
            elif line.startswith("# line-no: "):
                no = int(line[11:])
            else:
                new_program.add(no, line[:-1])
                no += 10
            first = False
        return new_program

    def save(self, path):
        hb = self.hash_bang or "#!/usr/bin/python3"
        # where line numbers do not follow the 10-increment pattern,
        # we add a line-no comment to set the line number
        def lines(items):
            yield hb # make files self-executable
            expected_no = 10
            for no in self.line_nos():
                if no != expected_no:
                    yield "# line-no: " + str(no)
                yield self._program[no]
                expected_no = no + 10
        with open(path, 'w') as f:
            f.writelines(line + '\n'
                         for line in lines(self._program))
        os.chmod(path, 0o777)
        self.path = arg
        self.hash_bang = hb

program = TheProgram()

class Runner:
    shell = code.InteractiveInterpreter(vars)

    def run(program):
        obj = compile('\n'.join(program.text()), 'program', mode='exec')
        run_vars = dict(vars)
        run_vars['__file__'] = program.path
        def exit(): # prevent program from exiting the environment
            raise KeyboardInterrupt
        run_vars['exit'] = exit # BUGBUG: This does not work.
        # TODO: __name__
        exec(obj, run_vars, run_vars)
        # Also, to ensure all objects get destroyed, maybe see this:
        # http://lucumr.pocoo.org/2011/2/1/exec-in-python/
        # indicating that Python explicitly delets vars before shutting down.

    def runsource(line):
        return Runner.shell.runsource(line)

#pyglexer = Python3Lexer()
lexer = PygmentsLexer(Python3Lexer)

def handle_exception(e):
    print("".join(traceback.format_exception(*sys.exc_info())))

# TODO: in case of error, we should throw, and catch this above
def handle_edit_command(line) -> bool: # -> True if handled
    global program
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
        if ((first is not None and first not in program._program) or
            (last  is not None and last  not in program._program)):
            handled_with_err("SyntaxError: no such line number")
            return None
        return (first, last)
    if cmd == "new":
        if arg is not None:
            return unexpected_arg()
        program = TheProgram()
        return True
    elif cmd == "renumber":
        if arg is not None:
            return unexpected_arg()
        program = program.renumbered()
        return True
    elif cmd == "del" and arg and re.compile('^[0-9-]').match(arg):
        r = parse_no_range(arg)
        if not r:
            return True # invalid, and error already printed
        for no in program.line_nos(range=r):
            program.erase(no)
        return True
    elif cmd == "list" and (not arg or re.compile('^[0-9-]').match(arg)):
        r = parse_no_range(arg)
        if not r:
            return True # invalid, and error already printed
        if len(program._program) == 0:
            return True # empty program
        for no in program.line_nos(range=r):
            no_tuple = (Token.Literal.Number.Integer, " {:5} ".format(no))
            prompt_toolkit.print_formatted_text(PygmentsTokens([no_tuple] + list(program.get_lexed(no))[:-1]))
        return True
        # old; remove:
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
        for no, lex_tuples in next_line(program._program):
            if not TheProgram.in_no_range(no, r):
                if shown:
                    break
                else:
                    continue
            no_tuple = (Token.Literal.Number.Integer, " {:5} ".format(no))
            print_formatted_text(PygmentsTokens([no_tuple] + lex_tuples))
            shown = True
        return True
    elif cmd == "run":
        if arg is None:
            try:
                Runner.run(program)
            except Exception as e:
                handle_exception(e)
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
            return True
        else: # run PATH
            handle_edit_command("load " + arg)
            handle_edit_command("run")
            return True
    elif cmd == "save":
        if arg is None:
            if program.path is None:
                return arg_expected()
            arg = program.path # default to last used pathname
        path = arg + ".py"
        program.save(path)
        print('Saved {} lines to'.format(len(self._program)), path)
        return True
    elif cmd == "load":
        if arg is None:
            return arg_expected()
        path = arg + ".py"
        program = TheProgram.load(path)
        print('Loaded {} lines from'.format(len(program._program)), path)
        return True
    return False

def handle_enter_line(line):
    add_line_pattern = re.compile('^  *([0-9]+) (.*)$') # note: must have at least one space; otherwise it's an expression
    m = add_line_pattern.match(line)
    if not m:
        return (None, line)
    g = m.groups()
    line_no = int(g[0])
    code = g[1]
    if code.lstrip(' ') == "": # user just hit enter
        return (None, "")
    program.add(line_no, code)
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
        line = program.try_get(no)
        if line:
            b.insert_text(line, move_cursor=False)
    else:
        b.insert_text(' ') # regular space

def determine_indent(prev_line): # TODO: make this less simplistic
    # TODO: the following are examples of what is not handled:
    #  - ':' and 'pass' vs. line-end comments
    #  - multi-line expressions (both indent inside, and see above)
    #  - return statement should unindent as well
    if prev_line is None:
        return 0
    indent = len(prev_line) - len(prev_line.lstrip(' '))
    if prev_line.endswith(':'):
        indent += 4
    elif prev_line.endswith('pass') and indent >= 4:
        indent -= 4
    return indent

history = InMemoryHistory()
session = prompt_toolkit.PromptSession(key_bindings=bindings,
                                       history=history,
                                       lexer=lexer)

def getline(last_edited_line, prev_line):
    prefix = "" # line number and indentation
    suffix = "" # existing line content
    if last_edited_line is not None:
        next_line_no = program.next_line_no_after(last_edited_line)
        prev_line = program.get(last_edited_line) # must exist
        prefix = " {:5} ".format(next_line_no)
        suffix = program.try_get(next_line_no) or ""
    try:
        if suffix == "":
            prefix += ' ' * determine_indent(prev_line)
        return session.prompt(default=prefix + suffix) # TODO: cursor at prefix
        # TODO: if all-blank line and no change made by user then return empty line
    except KeyboardInterrupt:
        return ""
 
import psutil
mem = psutil.virtual_memory().total
banner = "\n    **** BASIC PYTHON V1 ****\n\n{:,} BYTES FREE\n".format(mem)
print(banner)

while True:
    print("Ready.")
    last_edited_line = None
    line = getline(last_edited_line, None)
    (last_edited_line, line) = handle_enter_line(line)
    while last_edited_line is not None: # no READY between entered lines
        line = getline(last_edited_line, None)
        (last_edited_line, line) = handle_enter_line(line)
    if handle_edit_command(line):
        continue
    try:
        last_line = line
        while Runner.runsource(line):
            new_line = getline(None, last_line)
            line = line + '\n' + new_line
            last_line = new_line
    except Exception as e:
        handle_exception(e)
        pass
