# prerequisites:
#  - pip install prompt-toolkit     (2.0.9)
#  - pip install pygame             (1.9.4)
#  - pip install --upgrade psutil   (5.6.0)

from basicpython import repl

import pygterm64, pygame, sys
from pygame.locals import *
win = pygterm64.PygTerm64(50, 30, sysfont = ("Consolas", 20), half_height = False, fullscreen=True)
win.autoblit = False

class StdoutProxy:
    def __init__(self, win):
        self._win = win
        pass
    def write(self, s):
        self._win.write(s)
    def flush(self):
        pass

sys.stdout = StdoutProxy(win)
sys.stderr = StdoutProxy(win)

print('\x1b]0;Basic Python\x07', end='')

def getline(default : str, pos : int):
    if default is not None:
        print(default, end='\x01' + '\x1d' * pos) # prompt - Home - right arrow to start
    return win.input(prompt = None) # prompt = None means screen editor

def color_for(tokenType):
    if tokenType[0] == 'Literal':
        if tokenType[1] == 'Number':
            return '\x99' # lt green
        else:
            return '\x96' # lt red
    elif tokenType[0] == 'Keyword':
        return '\x9f' # cyan
    elif tokenType[0] == 'Name':
        return '\x9e' # yellow
    elif tokenType[0] == 'Comment':
        return '\x1e' # green
    elif tokenType[0] == 'Yellow':
        return '\x9f' # cyan
    else:
        return '\x9a' # lt blue

def escaped_token(token): # escape control chars embedded in a token (=string literal)
    return ''.join(('\x1b' + c) if c < ' ' or (c >= '\x80' and c <= '\x9f') else c for c in token)

def pretty_print(tokens):
    line = ''.join(color_for(t[0]) + escaped_token(t[1]) for t in tokens.token_list) + '\x9a'
    print(line)

repl(getline, pretty_print)

#print("Hit a key to continue: ", end='')
#ch = win.get()
#print(ch)
#name = win.input("What's your name?")
#print('Hello,', name)
#i = 0
#while True:
#    print("READY.")
#    line = win.input(prompt = None)
#    if line is None or line == 'exit':
#        break
#    try:
#        last_line = line
#        while Runner.runsource(line):
#            new_line = win.input(prompt = None)
#            line = line + '\n' + new_line
#            last_line = new_line
#    except Exception as e: # runsource catches all exceptions; this is just to be sure we won't die
#        report_exception(e)
#    continue
#    if i == 0:
#        print('print ("\x1b\x1cR\x1b\x9fA\x1b\x9cI\x1b\x1eN\x1b\x96B\x1b\x9eO\x1b\x81W")')
#
#        print('\x1cR\x9fA\x9cI\x1eN\x96B\x9eO\x81W\x9a')
#        print('READY.\n')
#
#        print('C64 COLORS:\n') # home
#        for col in [144,  5, 28,159,156, 30, 31,158,129,149,150,151,152,153,154,155]:
#            print(chr(col) + f"\x12\t\t\t\t\x92 {col:3}")
#    #    win.write("\x9f") # cyan
#    #    win.write(f'{i}\tevent.type == \x96\x12MOUSE\x92MOTION\x9f; x == MOUSEMOTION\n')
#    #if i % 120 == 0:
#    #    win.write('\x9eUse mouse to move line, arrow keys to move shadow, p to switch to fullscreen.\n')
#
#    win.tick()
#    win.blittowindow()
#    i += 1
