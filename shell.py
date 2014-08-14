"""Implement a simple shell for running on MicroPython."""

# from __future__ import print_function

import os
import sys
import cmd
import pyb

# TODO:
#   - Need to figure out how to get input without echo for term_size
#   - Add sys.stdin.isatty() for when we support reading from a file
#   - Need to integrate readline in a python callable way (into cmd.py)
#       so that the up-arrow works.
#   - Need to define input command to use this under windows


def term_size():
    """Print out a sequence of ANSI escape code which will report back the
    size of the window.
    """
    # ESC 7         - Save cursor position
    # ESC 8         - Restore cursor position
    # ESC [r        - Enable scrolling for entire display
    # ESC [row;colH - Move to cursor position
    # ESC [6n       - Device Status Report - send ESC [row;colR
    sys.stdout.write('\x1b7\x1b[r\x1b[999;999H\x1b[6n')
    # sys.stdout.flush()
    pos = ''
    while True:
        char = sys.stdin.read(1)
        if char == 'R':
            break
        if char != '\x1b' and char != '[':
            pos += char
    (height, width) = [int(i) for i in pos.split(';')]
    sys.stdout.write('\x1b8')
    # sys.stdout.flush()
    return height, width

# def term_size():
#    return (25, 80)


def print_cols(words, termwidth=79):
    """Takes a single column of words, and prints it as multiple columns that
    will fit in termwidth columns.
    """
    width = max([len(word) for word in words])
    nwords = len(words)
    ncols = max(1, (termwidth + 1) // (width + 1))
    nrows = (nwords + ncols - 1) // ncols
    for row in range(nrows):
        for i in range(row, nwords, nrows):
            print('%-*s' % (width, words[i]),
                  end='\n' if i + nrows >= nwords else ' ')


def sdcard_present():
    """Determine if the sdcard is present. This current solution is specific
    to the pyboard. We should really have a pyb.scard.detected() method
    or something.
    """
    return pyb.Pin.board.SD.value() == 0


class Shell(cmd.Cmd):
    """Implements the shell as a command line interpreter."""

    def __init__(self, **kwargs):
        (self.term_height, self.term_width) = term_size()
        cmd.Cmd.__init__(self, **kwargs)

        self.cur_dir = os.getcwd()
        self.set_prompt()

    def set_prompt(self):
        self.prompt = self.cur_dir + '> '

    def mode(self, filename):
        try:
            return os.stat(filename)[0]
        except OSError:
            return 0

    def mode_exists(self, mode):
        return mode & 0xc000 != 0

    def mode_isdir(self, mode):
        return mode & 0x4000 != 0

    def mode_isfile(self, mode):
        return mode & 0x8000 != 0

    def resolve_path(self, path):
        if path[0] != '/':
            # Relative path
            if self.cur_dir[-1] == '/':
                path = self.cur_dir + path
            else:
                path = self.cur_dir + '/' + path
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

    def emptyline(self):
        """We want empty lines to do nothing. By default they would repeat the
        previous command.

        """
        pass

    def postcmd(self, stop, line):
        self.set_prompt()
        return stop

    def line_to_args(self, line):
        """This will convert the line passed into the do_xxx functions into
        and array of arguments.
        """
        return line.split()

    def help_args(self):
        self.stdout.write('Prints out command line arguments.\n')

    def do_args(self, line):
        args = self.line_to_args(line)
        for idx in range(len(args)):
            print("arg[%d] = '%s'" % (idx, args[idx]))

    def help_cat(self):
        self.stdout.write('Concatinate files and send to stdout.\n')

    def do_cat(self, line):
        args = self.line_to_args(line)
        target = None
        if '>' in args:
            target = args[-1]
            target = self.resolve_path(target)
            mode = self.mode(target)
            if not self.mode_exists(mode):
                sys.stdout.write("Cannot access '%s': No such file\n" % target)
            if not self.mode_isfile(mode):
                sys.stdout.write("'%s': is not a file\n" % target)
            args = args[:-2]
        for filename in args:
            filename = self.resolve_path(filename)
            mode = self.mode(filename)
            if not self.mode_exists(mode):
                sys.stdout.write("Cannot access '%s': No such file\n" % filename)
                continue
            if not self.mode_isfile(mode):
                sys.stdout.write("'%s': is not a file\n" % filename)
                continue
            if target is None:
                with open(filename, 'r') as txtfile:
                    for line in txtfile:
                        print(line, end='')
                        print('')
            else:
                with open(filename, 'r') as txtfile:
                    with open(target, 'a') as outfile:
                        for line in txtfile:
                            outfile.write(line)

    def help_cd(self):
        self.stdout.write('Changes the current directory\n')

    def do_cd(self, line):
        args = self.line_to_args(line)
        try:
            dirname = self.resolve_path(args[0])
        except IndexError:
            dirname = '/'
        mode = self.mode(dirname)
        if self.mode_isdir(mode):
            self.cur_dir = dirname
        else:
            self.stdout.write("Directory '%s' does not exist\n" % dirname)

    def help_echo(self):
        self.stdout.write('Display a line of text.\n')

    def do_echo(self, line):
        args = self.line_to_args(line)
        target = None
        if '>' in args:
            target = args[-1]
            target = self.resolve_path(target)
            mode = self.mode(target)
            if not self.mode_exists(mode):
                sys.stdout.write("Cannot access '%s': No such file\n" % target)
            if not self.mode_isfile(mode):
                sys.stdout.write("'%s': is not a file\n" % target)
            args = args[:-2]
        if target is None:
            for word in args:
                print(word, end=' ')
            print('')
        else:
            with open(target, 'a') as outfile:
                for word in args:
                    word = word + ' '
                    outfile.write(word)
                outfile.write('\n')

    def help_help(self):
        self.stdout.write('List available commands with "help" or detailed ' +
                          'help with "help cmd".\n')

    def do_help(self, line):
        cmd.Cmd.do_help(self, line)

    def help_ls(self):
        self.stdout.write('List directory contents.\n' +
                          'Use ls -a to show hidden files')

    def do_ls(self, line):
        args = ['.']
        line_args = self.line_to_args(line)
        for arg in line_args:
            args.append(arg)
        show_invisible = False
        if len(args) > 1:
            if args[1] == '-a':
                show_invisible = True
                args = args[0:1]+args[2:]
        for idx in range(len(args)):
            dirname = self.resolve_path(args[idx])
            mode = self.mode(dirname)
            if not self.mode_exists(mode):
                sys.stdout.write("Cannot access '%s': No such file or directory\n" % dirname)
                continue
            if not self.mode_isdir(mode):
                sys.stdout.write(dirname)
                sys.stdout.write('\n')
                continue
            files = []
            vfiles = []
            if len(args) > 1:
                if idx > 0:
                    self.stdout.write('\n')
                self.stdout.write("%s:\n" % dirname)
            for filename in os.listdir(dirname):
                if dirname[-1] == '/':
                    full_filename = dirname + filename
                else:
                    full_filename = dirname + '/' + filename
                mode = self.mode(full_filename)
                if self.mode_isdir(mode):
                    filename += '/'
                files.append(filename)
                if (filename[0] != '.') and (filename[-1] != '~'):
                    vfiles.append(filename)
            if (len(files) > 0) and show_invisible:
                print_cols(sorted(files), self.term_width)
            if (len(vfiles) > 0) and not show_invisible:
                print_cols(sorted(vfiles), self.term_width)

    def help_micropython(self):
        self.stdout.write('Micropython! Call any scripts! Interactive mode! ' +
                          'Quit with exit()')

    def do_micropython(self, line):
        args = self.line_to_args(line)
        source = None
        if len(args) == 1:
            source = args[-1]
            source = self.resolve_path(source)
            mode = self.mode(source)
            if not self.mode_exists(mode):
                sys.stdout.write("Cannot access '%s': No such file\n" % source)
                return
            if not self.mode_isfile(mode):
                sys.stdout.write("'%s': is not a file\n" % source)
                return
        if source is None:
            print('[Micropython]')
            while True:
                code_str = '' 
                line = input('|>>> ')
                if line[0:4] == 'exit':
                    break
                code_str += '%s\n' % line
                if line[-1] == ':':
                    while True:                   
                        line = input('|... ')
                        if line == '':
                            break
                        code_str += '%s\n' % line
                exec(code_str)
        else:
            code_str = ''
            with open(source, 'r') as code:
                for line in code:
                    code_str = code_str + line + '\n'
            exec(code_str)

    def help_EOF(self):
        self.stdout.write('Control-D to quit.\n')

    def do_EOF(self, _):
        # The prompt will have been printed, so print a newline so that the
        # REPL prompt shows up properly.
        print('')
        return True


def run():
    Shell().cmdloop()

run()
