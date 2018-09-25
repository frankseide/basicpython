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
from bisect import bisect

class TheProgram:
    lexer = Python3Lexer()
    max_line_no = 99999

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
            return self.get(no)
        except:
            return None

    def get_lexed(self, no):
        # TODO: lex the whole thing, not just line by line
        # TODO: cache this
        return pygments.lex(self._program[no], TheProgram.lexer)

    def line_no_after(self, line_no, steps=1): # or None. line_no must exist
        nos = list(self.line_nos())
        i = nos.index(line_no) + steps # bisect_right(nos, line_no) or so
        if i < len(nos):
            return nos[i]
        else:
            return None

    def line_no_before(self, line_no): # or None. line_no may not exist
        nos = list(self.line_nos())
        i = bisect(nos, line_no) - 1
        if i >= 0:
            return nos[i]
        else:
            return None

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
        self.path = path
        self.hash_bang = hb

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

class Runner:
    shell = code.InteractiveInterpreter(vars)

    def run(program):
        obj = compile('\n'.join(program.text()), 'program', mode='exec')
        run_vars = dict(vars)
        run_vars['__file__'] = program.path
        def exit(): # prevent program from exiting the environment
            raise KeyboardInterrupt
        run_vars['exit'] = exit # BUGBUG: This does not work.
        old_exit = sys.exit
        try:
            sys.exit = exit # this works, but also affects our REPL; and will not free the program's resources
            # TODO: __name__
            exec(obj, run_vars, run_vars)
        finally:
            sys.exit = old_exit
            print('caught')
            # break circular references
            for key, val in run_vars.items():
                run_vars[key] = None
        # Also, to ensure all objects get destroyed, maybe see this:
        # http://lucumr.pocoo.org/2011/2/1/exec-in-python/
        # indicating that Python explicitly delets vars before shutting down.

    def runsource(line):
        return Runner.shell.runsource(line)

def report_exception(e):
    print("".join(traceback.format_exception(*sys.exc_info())))

class EditError(Exception): # handle_edit_command throws this in case of an error
    def __init__(self, msg):
        self.msg = msg

def fail(msg):
    raise EditError(msg)

def handle_edit_command(line) -> bool: # -> True if handled
    global program
    p = re.compile('^([a-z]+)( ?) *(.*)$')
    m  = p.match(line)
    if not m:
        return False
    cmd, space, arg = m.groups()
    if space == '' and arg != '':
        return False # e.g. 'save13 = 5'
    if arg == '':
        arg = None
    # helpers for validating and parsing 'arg'
    def validate_no_arg():
        if arg is not None:
            fail('SyntaxError: {} command unexpects no argument'.format(cmd))
    def required_arg():
        if arg is None:
            fail('SyntaxError: {} command requires an argument'.format(cmd))
        return arg
    def arg_as_range(arg) -> tuple:
        if arg is None:
            arg = ''
        p = re.compile('^([0-9]*) *([-,]?) *([0-9]*)$')
        m = p.match(arg)
        def malformed():
            fail("SyntaxError: mal-formed line number range '{}'".format(arg))
        if not m:
            malformed()
        first, dash, last = m.groups()
        first = int(first) if first != '' else None
        last  = int(last)  if last  != '' else first if dash == '' else None
        if dash == ',': # convert , expression. Number after comma is number of lines.
            if not last: # (None or 0)
                malformed()
            last = program.line_no_after(first, steps=last-1)
        def validate_optional_no(no):
            if (no is not None and no not in program._program):
                fail("ArgumentError: {} is not an existing line number".format(no))
        validate_optional_no(first)
        validate_optional_no(last)
        if first is not None and last is not None and first > last:
            malformed()
        return (first, last)
    def has_range_arg():
        return arg and re.compile('^[0-9]* *[-,]? *[0-9]*$').match(arg) # same re as above except ( )
    def has_symbol_arg():
        return arg and re.compile('^[a-zA-Z_][a-zA-Z0-9_]* *,? *[0-9]*$').match(arg)
    def list_lines(nos):
        for no in nos:
            no_tuple = (Token.Literal.Number.Integer, " {:5} ".format(no))
            prompt_toolkit.print_formatted_text(PygmentsTokens([no_tuple] + list(program.get_lexed(no))[:-1]))
    # handle command
    if cmd == "new":
        validate_no_arg()
        program = TheProgram()
    elif cmd == "renumber":
        validate_no_arg()
        program = program.renumbered()
    elif cmd == "del" and has_range_arg(): # note: match 'del' only with number range
        for no in program.line_nos(range=arg_as_range(arg)):
            program.erase(no)
        return True
    elif cmd == "find" and arg: # string or regex match
        if arg.startswith('/') and arg.endswith('/'):
            p = re.compile('.*' + arg[1:-1] + '.*') # TODO: how about this strange pinning to start?
        else:
            p = re.compile('.*' + re.escape(arg) + '.*')
        nos = (no for no in program.line_nos() if p.match(program.get(no)))
        list_lines(nos)
    elif cmd == "list" and (not arg or has_range_arg() or has_symbol_arg()): # note: match 'list' only with number range or without arg
        if has_symbol_arg(): # list classes and/or defs
            # TODO: Python re's are weird; they seem to imply ^ but not $
            p = re.compile('^([a-zA-Z_][a-zA-Z0-9_]*) *(,?) *([0-9]*)$')
            m = p.match(arg)
            arg, comma, max_count = m.groups()
            if comma != '':
                if max_count == '':
                    fail("SyntaxError: mal-formed line number range ',{}'".format(max_count))
                max_count = int(max_count)
            else:
                max_count = None
            if arg == "class" or arg == "def": # look for all class or def
                p = re.compile('.*\\b' + arg + '  *[a-zA-Z_][a-zA-Z0-9_]*.*')
                single = True
            else: # look for symbol definition
                #p = re.compile('.*\\b' + arg + '\\b.*')
                p = re.compile('.*\\b(def|class)\\b  *' + arg + '\\b.*')
                single = False
            print(p)
            def matching_lines():
                nonlocal max_count
                on = False
                indent = None
                re_empty = re.compile('^ *(|#.*)$')
                for no in program.line_nos():
                    line = program.get(no)
                    m = p.match(line)
                    if m:
                        on = True # note: nested matches get ignored w.r.t. indentation this way
                        # TODO: somehow insert a blank line between multiple matches
                    if on:
                        if single: # single match: and done.
                            on = False
                        elif not re_empty.match(line):
                            this_indent = len(line) - len(line.lstrip())
                            if indent is None:
                                indent = this_indent
                            elif this_indent <= indent: # reached next block on same indent level
                                on = False
                                indent = None
                                continue # skip outputting this line
                        yield no
                        # limit the number of lines
                        if max_count is not None:
                            max_count -= 1
                            if max_count <= 0:
                                break
                        # TODO: include preceding decorators
            nos = matching_lines()
        else: # list by line numbers
            nos = program.line_nos(range=arg_as_range(arg))
        list_lines(nos)
    elif cmd == "save":
        if arg is None:
            arg = program.path # default to last used pathname (will fail next if none yet)
        path = required_arg() + ".py"
        program.save(path)
        print('Saved {} lines to'.format(len(self._program)), path)
    elif cmd == "load":
        path = required_arg() + ".py"
        program = TheProgram.load(path)
        print('Loaded {} lines from'.format(len(program._program)), path)
    elif cmd == "run":
        if arg is None:
            Runner.run(program)
        else: # run PATH
            handle_edit_command("load " + arg)
            handle_edit_command("run")
    else:
        return False    # not handled
    return True         # handled as an edit command

def handle_enter_line(line):
    add_line_pattern = re.compile('^  *([0-9]+) (.*)$') # note: must begin with space; otherwise it's an expression
    m = add_line_pattern.match(line)
    if not m:
        return (None, line)
    g = m.groups()
    line_no, code = m.groups()
    line_no = int(line_no)
    if line_no > TheProgram.max_line_no:
        fail('ValueError: line number {} exceeds maximum allowed line number'.format(TheProgram.max_line_no))
    program.add(line_no, code)
    #print('line_no=', line_no, 'code=', code)
    return (line_no, line)

############################################################################## 
# Python-aware getline() function via PromptToolkit
############################################################################## 

def create_getline():
    # create bindings
    # We handle ' ' (to right-align line numbers and indent), Backspace (to unalign and unindent), and Esc
    bindings = KeyBindings()

    @bindings.add('escape')
    def _(event):
        # TODO: somehow user must press Esc twice; not optimal
        b = event.current_buffer
        b.transform_current_line(lambda _: "")

    @bindings.add(' ')
    def _(event):
        global program
        p = re.compile('^( *)([0-9]+)$')
        b = event.current_buffer
        m = p.match(b.text)
        if m: # TODO: check if we are at line end --  space after line number
            space, no_str = m.groups()
            spaces_needed = 6 - len(space) - len(no_str)
            if spaces_needed > 0:
                b.delete_before_cursor(len(no_str))
                b.insert_text(' ' * spaces_needed + no_str, overwrite=True)
            b.insert_text(' ') # insert the actual space
            # if line exists then bring it into the editor
            no = int(no_str)
            line = program.try_get(no)
            if line:
                b.insert_text(line, move_cursor=False)
            # else if it does not exist, then check the previous line and indent
            else:
                prev_no = program.line_no_before(no)
                indent = TheProgram.determine_indent(prev_no and program.get(prev_no))
                b.insert_text(' ' * indent)
        else:
            b.insert_text(' ') # regular space

    @bindings.add('c-h')
    def _(event):
        p = re.compile('^( *)([0-9]+) $')
        b = event.current_buffer
        m = p.match(b.text)
        if m and len(b.text) == 7: # DEL right after line number: undo leading spaces, so one can type expressions
            space, no_str = m.groups()
            b.delete_before_cursor(len(b.text)) # delete all
            b.insert_text(no_str) # reinsert plain number
        else:
            # delete indentation
            if b.text.endswith('    '):
                b.delete_before_cursor(4) # unindent
            else:
                b.delete_before_cursor(1)

    # create lexer for syntax highlighting
    lexer = PygmentsLexer(Python3Lexer)

    # create PromptSession. This is the line editor.
    prompt_session = prompt_toolkit.PromptSession(key_bindings=bindings,
                                                  history=InMemoryHistory(),
                                                  lexer=lexer)

    # this is the getline() function we return
    def getline(last_entered_line_no, prev_line):
        global program
        prefix = "" # line number and indentation
        suffix = "" # existing line content
        if last_entered_line_no is not None:
            next_line_no = program.line_no_after(last_entered_line_no) or last_entered_line_no + 10
            next_line_no = min(next_line_no, last_entered_line_no + 10)
            if next_line_no <= TheProgram.max_line_no:
                prev_line = program.get(last_entered_line_no) # for indent. Known to exist.
                prefix = " {:5} ".format(next_line_no)
                suffix = program.try_get(next_line_no) or "" # get existing line into edit buffer
        try:
            if suffix == "":    # auto-indent
                prefix += ' ' * TheProgram.determine_indent(prev_line)
            line = prompt_session.prompt(default=prefix + suffix) # TODO: cursor at prefix
            # TODO: if all-blank line and no change made by user then return empty line
            any_edits = line != prefix + suffix
            if not any_edits and suffix == "":
                return ""
            return line
        except KeyboardInterrupt:
            return ""
    return getline

############################################################################## 
# main loop
############################################################################## 

getline = create_getline()

program = TheProgram()

import psutil
mem = psutil.virtual_memory().total
banner = "\n    **** BASIC PYTHON V1 ****\n\n{:,} BYTES FREE\n".format(mem)
print(banner)

while True:
    # fetch line with READY prompt
    print("Ready.")
    last_entered_line_no = None
    line = getline(last_entered_line_no, None)

    # handle entering a line (starts with space then number)
    try:
        (last_entered_line_no, line) = handle_enter_line(line)
        while last_entered_line_no is not None: # no READY prompt when entering multiple lines
            line = getline(last_entered_line_no, None)
            (last_entered_line_no, line) = handle_enter_line(line)
    except EditError as e: # we get here if the line number was too large
        print(e.msg)
        continue

    # not a line being entered: maybe an editing keyword?
    try:
        if handle_edit_command(line):
            continue
    except EditError as e: # we get here if it was an edit command that failed
        print(e.msg)
        continue
    except KeyboardInterrupt: # e.g. Ctrl-C during list
        print('KeyboardInterrupt')
        continue
    except Exception as e: # error during execution, e.g. file not found
        report_exception(e)
        continue

    # no editing keyword: regular Python code
    try:
        last_line = line
        while Runner.runsource(line):
            new_line = getline(None, last_line)
            line = line + '\n' + new_line
            last_line = new_line
    except Exception as e: # runsource catches all exceptions; this is just to be sure we won't die
        report_exception(e)
