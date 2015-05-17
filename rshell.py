#!/usr/bin/env python3

"""Implement a remote shell which talks to a MicroPython board.

   This program uses the raw-repl feature of the pyboard to send small
   programs to the pyboard to carry out the required tasks.
"""

# from __future__ import print_function

import argparse
import cmd
from getch import getch
import inspect
import os
import pyboard
import select
import shutil
import sys
import time

MONTH = ('', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

# Attributes
# 0	Reset all attributes
# 1	Bright
# 2	Dim
# 4	Underscore
# 5	Blink
# 7	Reverse
# 8	Hidden

LT_BLACK    = "\x1b[1;30m"
LT_RED      = "\x1b[1;31m"
LT_GREEN    = "\x1b[1;32m"
LT_YELLOW   = "\x1b[1;33m"
LT_BLUE     = "\x1b[1;34m"
LT_MAGENTA  = "\x1b[1;35m"
LT_CYAN     = "\x1b[1;36m"
LT_WHITE    = "\x1b[1;37m"

DK_BLACK    = "\x1b[2;30m"
DK_RED      = "\x1b[2;31m"
DK_GREEN    = "\x1b[2;32m"
DK_YELLOW   = "\x1b[2;33m"
DK_BLUE     = "\x1b[2;34m"
DK_MAGENTA  = "\x1b[2;35m"
DK_CYAN     = "\x1b[2;36m"
DK_WHITE    = "\x1b[2;37m"

NO_COLOR    = "\x1b[0m"

DIR_COLOR    = LT_CYAN
PROMPT_COLOR = LT_GREEN
PY_COLOR     = DK_GREEN
END_COLOR    = NO_COLOR

pyb = None
pyb_root_dirs = []
cur_dir = ''

IS_UPY = False
debug = False

# CPython uses Jan 1, 1970 as the epoch, where MicroPython uses Jan 1, 2000
# as the epoch. TIME_OFFSET is the constant number of seconds needed to
# convert from one timebase to the other.
TIME_OFFSET = time.mktime((2000, 1, 1, 0, 0, 0, 0, 0, 0))

def resolve_path(path):
    """Resolves path and converts it into an absolute path."""
    if path[0] != '/':
        # Relative path
        if cur_dir[-1] == '/':
            path = cur_dir + path
        else:
            path = cur_dir + '/' + path
    comps = path.split('/')
    new_comps = []
    for comp in comps:
        if comp == '.':
            continue
        if comp == '..' and len(new_comps) > 1:
            new_comps.pop()
        else:
            new_comps.append(comp)
    if len(new_comps) == 1:
        return new_comps[0] + '/'
    return '/'.join(new_comps)


def is_remote_path(filename):
    """Determines if a given file is located locally or remotely. We assume
       that any directories from the pyboard take precendence over local
       directories of the same name. Currently, the pyboard can have /flash
       and /sdcard.
    """
    test_filename = filename + '/'
    for root_dir in pyb_root_dirs:
        if test_filename.startswith(root_dir):
            return   True
    return False


def remote_repr(i):
    """Helper function to deal with types which we can't send to the pyboard."""
    repr_str = repr(i)
    if repr_str and repr_str[0] == '<':
        return 'None'
    return repr_str


def remote(func, *args, xfer_func=None, **kwargs):
    """Calls func with the indicated args on the micropython board."""
    args_arr = [remote_repr(i) for i in args]
    kwargs_arr = ["{}={}".format(k, remote_repr(v)) for k,v in kwargs.items()]
    func_str = inspect.getsource(func)
    func_str += 'IS_UPY = True\n'
    func_str += 'output = ' + func.__name__ + '('
    func_str += ', '.join(args_arr + kwargs_arr)
    func_str += ')\n'
    func_str += 'if output is not None:\n'
    func_str += '    print(output)\n'
    if debug:
        print('----- About to send the following to the pyboard -----')
        print(func_str)
        print('-----')
    pyb.enter_raw_repl()
    output = pyb.exec_raw_no_follow(func_str)
    if xfer_func:
        xfer_func(*args, **kwargs)
    output, err = pyb.follow(timeout=10)
    pyb.exit_raw_repl()
    if debug:
        print('-----Response-----')
        print(output)
        print('-----')
    return output


def remote_eval(func, *args, **kwargs):
    """Calls func with the indicated args on the micropython board, and
       converts the response back into python by using eval.
    """
    return eval(remote(func, *args, **kwargs))


def print_bytes(byte_str):
    """Prints a string or converts bytes to a string and then prints."""
    if isinstance(byte_str, str):
        print(byte_str)
    else:
        print(str(byte_str, encoding='utf8'))


def auto(func, filename, *args, **kwargs):
    """If `filename` is a remote file, then this function calls func on the
       micropython board, otherwise it calls it locally.
    """
    if is_remote_path(filename):
        return remote_eval(func, filename, *args, **kwargs)
    return func(filename, *args, **kwargs)


def cat(src_filename, dst_file):
    """Copies the contents of the indicated file to an already opened file."""
    if is_remote_path(src_filename):
        filesize = remote_eval(get_filesize, src_filename)
        return remote(send_file_to_host, src_filename, dst_file, filesize,
                      xfer_func=recv_file_from_remote)
    with open(src_filename, 'r') as txtfile:
        for line in txtfile:
            dst_file.write(line)


def copy_file(src_filename, dst_filename):
    """Copies a file from one place to another. Both the source and destination
       files must exist on the same machine.
    """
    try:
        with open(src_filename, 'rb') as src_file:
            with open(dst_filename, 'wb') as dst_file:
                while True:
                    buf = src_file.read(512)
                    if len(buf) > 0:
                        dst_file.write(buf)
                    if len(buf) < 512:
                        break
        return True
    except:
        return False


def cp(src_filename, dst_filename):
    """Copies one file to another. The source file may be local or remote and
       the destnation file may be local or remote.
    """
    src_is_remote = is_remote_path(src_filename)
    dst_is_remote = is_remote_path(dst_filename)
    if src_is_remote == dst_is_remote:
        return auto(copy_file, src_filename, dst_filename)
    filesize = auto(get_filesize, src_filename)
    if src_is_remote:
        with open(dst_filename, 'wb') as dst_file:
            return remote(send_file_to_host, src_filename, dst_file, filesize,
                          xfer_func=recv_file_from_remote)
    with open(src_filename, 'rb') as src_file:
        return remote(recv_file_from_host, src_file, dst_filename, filesize,
                      xfer_func=send_file_to_remote)


def eval_str(str):
    """Executes a string containing python code."""
    output = eval(str)
    return output


def get_filesize(filename):
    """Returns the size of a file, in bytes."""
    import os
    try:
        return os.stat(filename)[6]
    except OSError:
        return -1


def get_mode(filename):
    """Returns the mode of a file, which can be used to determine if a file
       exists, if a file is a file or a directory.
    """
    import os
    try:
        return os.stat(filename)[0]
    except OSError:
        return 0


def get_stat(filename):
    """Returns the stat array for a given file. Returns all 0's if the file
       doesn't exist.
    """
    try:
        import os
        rstat = os.stat(filename)
        if IS_UPY:
            # Micropython dates are relative to Jan 1, 2000. On the host, time
            # is relative to Jan 1, 1970.
            return rstat[:6] + tuple(tim + TIME_OFFSET for tim in rstat[7:])
        return rstat
    except OSError:
        return (0, 0, 0, 0, 0, 0, 0, 0)


def listdir(dirname):
    """Returns a list of filenames contained in the named directory."""
    import os
    return os.listdir(dirname)


def listdir_stat(dirname):
    """Returns a list of tuples for each file contained in the named
       directory. Each tuple contains the filename, followed by the tuple
       returned by calling os.stat on the filename.
    """
    import os
    return tuple((file, os.stat(file)) for file in os.listdir(dirname))


def mkdir(files):
    """Creates one or more directories."""
    import os
    for file in files:
        try:
            os.mkdir(dirname)
        except:
            return False
    return True


def rm(filename):
    """Removes a file or directory."""
    import os
    try:
        os.remove(filename)
    except:
        try:
            os.rmdir(filename)
        except:
            return False
    return True


def recv_file_from_host(src_file, dst_filename, filesize):
    """Function which runs on the pyboard. Matches up with send_file_to_remote."""
    import sys
    if True:
        with open(dst_filename, 'wb') as dst_file:
            bytes_remaining = filesize
            while bytes_remaining > 0:
                read_size = min(bytes_remaining, 512)
                buf_remaining = read_size
                while buf_remaining > 0:
                    buf = sys.stdin.buffer.read(buf_remaining)
                    dst_file.write(buf)
                    buf_remaining -= len(buf)
                bytes_remaining -= read_size
                # Send back an ack as a form of flow control
                sys.stdout.buffer.write(b'\x06')
        return True
    #except:
    #    return False


def send_file_to_remote(src_file, dst_filename, filesize):
    """Intended to be passed to the `remote` function as the xfer_func argument.
       Matches up with recv_file_from_host.
    """
    bytes_remaining = filesize
    while bytes_remaining > 0:
        read_size = min(bytes_remaining,  512)
        buf = src_file.read(read_size)
        print('Sending %d bytes to remote' % len(buf))
        pyb.serial.write(buf)
        # Wait for ack so we don't get too far ahead of the remote
        while True:
            ch = pyb.serial.read(1)
            if ch == b'\x06':
                break
            sys.stdout.write(chr(ord(ch)))
        bytes_remaining -= read_size


def recv_file_from_remote(src_filename, dst_file, filesize):
    """Intended to be passed to the `remote` function as the xfer_func argument.
       Matches up with send_file_to_host.
    """
    bytes_remaining = filesize
    while bytes_remaining > 0:
        read_size = min(bytes_remaining,  512)
        buf_remaining = read_size
        while buf_remaining > 0:
            buf = pyb.serial.read(buf_remaining)
            dst_file.write(buf)
            buf_remaining -= len(buf)
        # Send an ack to the remote as a form of flow control
        pyb.serial.write(b'\x06')   # ASCII ACK is 0x06
        bytes_remaining -= read_size


def send_file_to_host(src_filename, dst_file, filesize):
    """Function which runs on the pyboard. Matches up with recv_file_from_remote."""
    import sys
    try:
        with open(src_filename, 'rb') as src_file:
            bytes_remaining = filesize
            while bytes_remaining > 0:
                read_size = min(bytes_remaining, 512)
                buf = src_file.read(read_size)
                sys.stdout.buffer.write(buf)
                bytes_remaining -= read_size
                # Wait for an ack so we don't get ahead of the remote
                while (len(sys.stdin.buffer.read(1)) == 0):
                    pass
        return True
    except:
        return False


def test_buffer():
    """Checks the micropython firmware to see if sys.stdin.buffer exists."""
    import sys
    try:
        x = sys.stdin.buffer
        return True
    except:
        return False


def mode_exists(mode):
    return mode & 0xc000 != 0


def mode_isdir(mode):
    return mode & 0x4000 != 0


def mode_isfile(mode):
    return mode & 0x8000 != 0


def word_len(word):
    """Returns the word lenght, minus any color codes."""
    if word[0] == '\x1b':
        return len(word) - 11   # 7 for color, 4 for no-color
    return len(word)

def print_cols(words, termwidth=79):
    """Takes a single column of words, and prints it as multiple columns that
    will fit in termwidth columns.
    """
    width = max([word_len(word) for word in words])
    nwords = len(words)
    ncols = max(1, (termwidth + 1) // (width + 1))
    nrows = (nwords + ncols - 1) // ncols
    for row in range(nrows):
        for i in range(row, nwords, nrows):
            word = words[i]
            if word[0] == '\x1b':
                print('%-*s' % (width + 11, words[i]),
                      end='\n' if i + nrows >= nwords else ' ')
            else:
                print('%-*s' % (width, words[i]),
                      end='\n' if i + nrows >= nwords else ' ')


def decorated_filename(filename, stat):
    """Takes a filename and the stat info and returns the decorated filename.
       The decoration takes the form of a single character which follows
       the filename. Currently, the only decodation is '/' for directories.
    """
    mode = stat[0]
    if mode_isdir(mode):
        return DIR_COLOR + filename + END_COLOR + '/'
    if filename.endswith('.py'):
        return PY_COLOR + filename + END_COLOR
    return filename


def is_hidden(filename):
    """Determines if the file should be considered to be a "hidden" file."""
    return filename[0] == '.' or filename[-1] == '~'

def is_visible(filename):
    """Just a helper to hide the double negative."""
    return not is_hidden(filename)


def print_long(filename, stat):
    """Prints detailed information about the file passed in."""
    size = stat[6]
    mtime = stat[8]
    localtime = time.localtime(mtime)
    print('%6d %s %2d %02d:%02d %s' % (size, MONTH[localtime[1]],
          localtime[2], localtime[4], localtime[5],
          decorated_filename(filename, stat)))


def trim(docstring):
    """Trims the leading spaces from docstring comments.

    From http://www.python.org/dev/peps/pep-0257/

    """
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


class Shell(cmd.Cmd):
    """Implements the shell as a command line interpreter."""

    def __init__(self, **kwargs):
        cmd.Cmd.__init__(self, **kwargs)

        self.stdout_to_shell = self.stdout

        global cur_dir
        cur_dir = os.getcwd()
        self.set_prompt()
        self.columns = shutil.get_terminal_size().columns

    def set_prompt(self):
        self.prompt = PROMPT_COLOR + cur_dir + END_COLOR + '> '

    def cmdloop(self, line=None):
        if line:
            self.onecmd(line)
        else:
            cmd.Cmd.cmdloop(self)

    def emptyline(self):
        """We want empty lines to do nothing. By default they would repeat the
        previous command.

        """
        pass

    def postcmd(self, stop, line):
        if self.stdout != self.stdout_to_shell:
            self.stdout.close()
            self.stdout = self.stdout_to_shell
        self.set_prompt()
        return stop

    def line_to_args(self, line):
        """This will convert the line passed into the do_xxx functions into
        an array of arguments and handle the Output Redirection Operator.
        """
        args = line.split()
        if '>' in args:
            self.stdout = open(args[-1], 'a')
            return args[:-2]
        else:
            return args

    def do_args(self, line):
        """Prints out command line arguments."""
        args = self.line_to_args(line)
        for idx in range(len(args)):
            print("arg[%d] = '%s'" % (idx, args[idx]))

    def do_cat(self, line):
        """cat filename...

           Concatinate files and send to stdout.
        """
        # Note: when we get around to supporting cat from stdin, we'll need
        #       to write stdin to a temp file, and then copy the file
        #       since we need to know the filesize when copying to the pyboard.
        args = self.line_to_args(line)
        for filename in args:
            filename = resolve_path(filename)
            mode = auto(get_mode, filename)
            if not mode_exists(mode):
                self.stdout.write("Cannot access '%s': No such file\n" %
                                  filename)
                continue
            if not mode_isfile(mode):
                self.stdout.write("'%s': is not a file\n" % filename)
                continue
            cat(filename, self.stdout.buffer)

    def do_cd(self, line):
        """Changes the current directory."""
        args = self.line_to_args(line)
        try:
            dirname = resolve_path(args[0])
        except IndexError:
            dirname = '/'
        mode = auto(get_mode, dirname)
        if mode_isdir(mode):
            global cur_dir
            cur_dir = dirname
        else:
            self.stdout.write("Directory '%s' does not exist\n" % dirname)

    def do_cp(self, line):
        """cp SOURCE DEST
           cp SOURCE... DIRECTORY

           Copies the SOURCE file to DEST. DEST may be a filename or a
           directory name. If more than one source file is specified, then
           the destination should be a directory.
        """
        args = self.line_to_args(line)
        if len(args) < 2:
            self.stdout.write('Missing desintation file\n')
            return
        dst_dirname = resolve_path(args[-1])
        dst_mode = auto(get_mode, dst_dirname)
        for src_filename in args[:-1]:
            src_filename = resolve_path(src_filename)
            if mode_isdir(dst_mode):
                dst_filename = dst_dirname + '/' + os.path.basename(src_filename)
            else:
                dst_filename = dst_dirname
            if not cp(src_filename, dst_filename):
                self.stdout.write("Unable to copy '%s' to '%s'\n"
                                  % (src_filename, dst_filename))
                break

    def do_echo(self, line):
        """Display a line of text."""
        args = self.line_to_args(line)
        self.stdout.write(args[0])
        self.stdout.write('\n')

    def do_help(self, line):
        """List available commands with "help" or detailed ' +
           'help with "help cmd".
        """
        # We provide a help function so that we can trim the leading spaces
        # from the docstrings. The builtin help function doesn't do that.
        if not line:
            return cmd.Cmd.do_help(self, line)
        try:
            doc = getattr(self, 'do_' + line).__doc__
            if doc:
                self.stdout.write("%s\n" % trim(doc))
                return
        except AttributeError:
            pass
        self.stdout.write("%s\n" % str(self.nohelp % (line,)))
        return

    def do_ls(self, line):
        """'List directory contents.

        'Use ls -a to show hidden files."""
        args = self.line_to_args(line)
        show_invisible = False
        show_long = False
        while len(args) > 0 and args[0][0] == '-':
            if args[0] == '-a':
                show_invisible = True
            elif args[0] == '-l':
                show_long = True
            else:
                self.stdout.write("Unrecognized option '%s'" % args[0])
                return
            args.remove(args[0])
        if len(args) == 0:
            args.append('.')
        for idx in range(len(args)):
            dirname = resolve_path(args[idx])
            mode = auto(get_mode, dirname)
            if not mode_exists(mode):
                self.stdout.write("Cannot access '%s': No such file or "
                                  "directory\n" % dirname)
                continue
            if not mode_isdir(mode):
                self.stdout.write(dirname)
                self.stdout.write('\n')
                continue
            if len(args) > 1:
                if idx > 0:
                    self.stdout.write('\n')
                self.stdout.write("%s:\n" % dirname)
            files = []
            for filename, stat in sorted(auto(listdir_stat, dirname),
                                         key=lambda entry: entry[0]):
                if is_visible(filename) or show_invisible:
                    if show_long:
                        print_long(filename, stat)
                    else:
                        files.append(decorated_filename(filename, stat))
            if len(files) > 0:
                print_cols(sorted(files), self.columns)

    def repl_serial_to_stdout(self):
        save_timeout = pyb.serial.timeout
        # Set a timeout so that the read returns periodically with no data
        # and allows us to check whether the main thread wants us to quit.
        pyb.serial.timeout = 1
        while not self.quit_serial_reader:
            ch = pyb.serial.read(1)
            if not ch:
                # This means that the read timed out. We'll check the quit
                # flag and return if needed
                continue
            self.stdout.write(chr(ord(ch)))
            self.stdout.flush()
        pyb.serial.timeout = save_timeout

    def do_repl(self, line):
        """Send character through to the regular repl."""
        self.stdout.write('Entering REPL. Use Control-D to exit.\n')
        import threading
        self.quit_serial_reader = False
        t = threading.Thread(target=self.repl_serial_to_stdout)
        t.daemon = True
        t.start()
        # Wake up the prompt
        pyb.serial.write(b'\n')
        while True:
            ch = getch()
            if not ch:
                continue
            if ch == b'\x04':
                self.quit_serial_reader = True
                break
            if ch == b'\n':
                pyb.serial.write(b'\r')
            else:
                pyb.serial.write(ch)
            pyb.serial.flush()
        t.join()

    def do_mkdir(self, line):
        """Create directory."""
        args = self.line_to_args(line)
        if not auto(mkdir(args)):
            print('Unable to create', args)

    def do_rm(self, line):
        """"rm FILE...

           Removes files or directories (directories must be empty).
        """
        args = self.line_to_args(line)
        for filename in args:
            filename = resolve_path(filename)
            if not auto(rm, filename):
                print('Unable to remove', filename)
                break

    def do_EOF(self, _):
        """Control-D to quit."""
        # The prompt will have been printed, so print a newline so that the
        # REPL prompt shows up properly.
        print('')
        return True


def main():
    """The main program."""
    default_baud = 115200
    default_port = os.getenv("RSHELL_PORT")
    if not default_port:
        default_port = '/dev/ttyACM0'
    parser = argparse.ArgumentParser(
        prog="rshell",
        usage="%(prog)s [options] [command]",
        description="Remote Shell for a MicroPython board.",
        epilog=("You can specify the default serial port using the " +
                "RSHELL_PORT environment variable.")
    )
    #parser.add_argument(
    #    "-b", "--baud",
    #    dest="baud",
    #    action="store",
    #    type=int,
    #    help="Set the baudrate used (default = %d)" % default_baud,
    #    default=default_baud
    #)
    parser.add_argument(
        "-p", "--port",
        dest="port",
        help="Set the serial port to use (default '%s')" % default_port,
        default=default_port
    )
    parser.add_argument(
        "-f", "--file",
        dest="filename",
        help="Specifies a file of commands to process."
    )
    parser.add_argument(
        "-d", "--debug",
        dest="debug",
        action="store_true",
        help="Enable debug features",
        default=False
    )
    parser.add_argument(
        "-n", "--nocolor",
        dest="nocolor",
        action="store_true",
        help="Turn off colorized output",
        default=False
    )
    parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        action="store_true",
        help="Turn on verbose messages",
        default=False
    )
    parser.add_argument(
        "cmd",
        nargs="*",
        help="Optional command to execute"
    )
    args = parser.parse_args(sys.argv[1:])

    if args.verbose:
        #prnt("Baud = %d" % args.baud)
        print("Port = %s" % args.port)
        print("Debug = %s" % args.debug)
        print("Cmd = [%s]", ', '.join(args.cmd))

    global debug
    debug = args.debug

    if args.nocolor:
        global DIR_COLOR, PROMPT_COLOR, PY_COLOR, END_COLOR
        DIR_COLOR = ''
        PROMPT_COLOR = ''
        PY_COLOR = ''
        END_COLOR = ''

    global pyb
    pyb = pyboard.Pyboard(args.port)

    global pyb_root_dirs
    pyb_root_dirs = ['/{}/'.format(dir) for dir in remote_eval(listdir, '/')]

    if not remote_eval(test_buffer):
        print("This program needs MicroPython firmware with sys.stdout.buffer")
        return

    if args.filename:
        with open(args.filename) as cmd_file:
            shell = Shell(stdin=cmd_file, filename=args.filename)
            shell.cmdloop('')
    else:
        shell = Shell()
        shell.cmdloop(' '.join(args.cmd))


main()
