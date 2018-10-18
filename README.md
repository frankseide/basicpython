`basicpython` is an interactive Python shell (aka Read-Eval-Print-Loop, or REPL) that also allows to
**edit and run small programs inside of the REPL** using **BASIC-style
line-number based code editing**.

As someone who grew up with the BASIC computers of the 80s, I always appreciated
the directness of those simple 8-bit systems, where one lived in a single shell
that would allow to experiment with BASIC statements interactively, edit
programs, and perform OS functions such as listing a directory, all in one
place.

Now, BASIC is not a particularly great language, but the line-number based
editing approach is amazingly powerful and easy to use as long as the program
does not grow too large.

The Python language improves on BASIC in many ways. I would even say, Python is
BASIC done right. But Python lacks this directness, because one cannot edit and
run Python code from *inside* the interactive Python session. You need a
separate text editor, and a separate shell like bash to run programs.

`basicpython` extends the Python REPL to allow you to enter a small program
directly using line numbers, `list` it, `save` it to disk, and `run` it right
there. For nostalgic reasons, it also replaces the `>>>` prompt with a friendly
`READY.`

### Entering code

To enter code lines, prepend line numbers. For example, entering the following
into `basicpython` will create a 2-line Python program in memory:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
10 for i in range(3):
20     print(i)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any code typed with a line number will not be executed, but rather remembered
under that number.

It is common to increment the line numbers in steps of 10, so that you can
insert lines later.

In Python, indentation matters. As you type the line numbers, `basicpython`
automatically inserts spaces before the number, such that e.g. line numbers 90
and 100, despite having different numbers of digits, line up.

For convenience, once you entered a line, you don’t need to type subsequent line
numbers: the system will automatically prompt you with the next line number. If
the previous line opened a new block (like `for`), it will also automatically
insert 4 spaces for you. After typing the above, you will be prompted to enter
line 30; just hit `Esc`. So you actually only type the following: `10 for i in
range(3):<Enter>print(i)<Enter><Esc>`, but what you will see on the screen is
this:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
    10 for i in range(3): # the spaces before the number are not typed by you
    20     print(i)       # the '20' and four spaces are not typed by you
    30                    # hit Esc here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This way, you can enter any valid Python program, including defining functions
and classes, and importing modules.

### Listing your code

To review the program, use the `list` command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
list
    10 for i in range(3):
    20     print(i)
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also give a line range to the `list` command. E.g. `list 100-200` will
only list lines 100 to 200. Alternatively, you can tell it how many lines to
list by using a comma instead of a hyphen: `list 100,10` would list the first 10
lines starting from line 100.

### Running your code

To run your program, type `run` and hit the `Enter` key:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
run
0
1
2
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### Changing your code

To add new lines, just enter them as described above. To *insert* a new line
between two existing ones, use a line number between the existing lines. For
example:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
15     print('----')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you type this and hit `enter`, you will be automatically shown the next
line (20) and placed in it to modify it. Since you don’t want to change it,
press the `Esc` key. You can now `list` the program to verify that the new line
is there:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
list
    10 for i in range(3):
    15     print('----')
    20     print(i)
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To change an existing line, just enter its line number and hit the space bar.
When you type a line number that already exists, `basicpython` will
automatically bring that line onto the screen, as if you just typed it again,
and allow you to edit it.

Try it: type `10` followed by a space. You will see this:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    10 for i in range(3):  # the cursor is positioned on the 'f'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now use the cursor keys to navigate to the `3` and change it to a `5`, then hit
the `Enter` key.

To delete a line, use the `del` command. For example, delete line 15 by typing
`del 15`, then `list` the program again:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
del 15
READY.
list
    10 for i in range(3):
    20     print(i)
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Like `list`, the `del` command also allows to specify ranges of line numbers.

### Saving and loading

You can save your program into a file using the `save` command, and load it back
using `load`, which will overwrite any current program in memory. For example,
let’s save the above program:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
save my_first_program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This will now be saved under the name `my_first_program.py` in your working
directory. The saved file is actually a valid Python script that can also be
executed from outside of `basicpython`.

Let’s add a new line:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
15     print('----')
<Esc>
list
    10 for i in range(3):
    15     print('----')
    20     print(i)
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

But now let's reload it, to show that this will overwrite the change you just
made:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
load my_first_program
READY.
list
    10 for i in range(3):
    20     print(i)
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also combine the `load` and `run` command into a single line:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
run my_first_program
0
1
2
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that, like `load`, this will also overwrite any existing unsaved program in
memory, and keep the newly loaded program in memory for further editing.

### Advanced functionality

If your program contains function definitions and/or classes, the `list` command
also allows you to list all function or class definitions using `list def` and
`list class`, respectively. This gives you sort of a table of content. You can
then list any function or class by name, for example `list Bullet`. Assuming
your code contains a class called `Bullet`, this will list the lines containing
the class definition. Further, you can select specific functions inside a class
(or functions defined inside other functions) using dot notation, for example
`list Bullet.__init__`. The listing can also be limited to the first number of
lines, e.g. `list main,10`.

A more generic search operation is the `find` command, which allows you to list
all lines containing a specific symbol. For example, `find i` will list all
lines using a variable or function or type called `i`. Alternatively, the `find`
command also allows to find arbitrary text by using regular expressions. For
example:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
READY.
find /int/
    20     print(i)
READY.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you attempt to insert code lines but find yourself having run out of line
numbers, you can use the `renumber` command to renumber the entire program
starting from 10 in increments of 10.

### Prerequisites

To use `basicpython`, you need to install a Python library called
`prompt_toolkit`. As of this writing, installing the right version of it
requires a special command as shown here:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pip3 install -e git+https://github.com/jonathanslenders/python-prompt-toolkit@2.0.4#egg=prompt_toolkit
pip3 install pygments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Then fetch `basicpython` with git:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
git clone https://github.com/frankseide/basicpython.git
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### Starting `basicpython`

Once you have installed the above prerequisites, run the following command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
basicpython/basicpython.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This will take you into the Python REPL that has the additional commands described above.
You should see this friendly message and are ready to type away:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    **** BASIC PYTHON V1 ****

270,378,254,336 BYTES FREE

READY.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Windows, the command to run is this:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
python basicpython\basicpython.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
