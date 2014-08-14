upy-shell
=========

MicroPython shell

This is a very simple command line based shell for MicroPython.
It is based on a stripped down version of cmd, which can be found
here: https://github.com/micropython/micropython-lib/pull/4

I use it by copying cmd.py an shell.py to my sdcard.
Then you can do:
```python
import shell
```
This will automatically run it. If you want to reinvoke it, then use:
```python
shell.run()
```

The shell has a notion of current directory, and you can use the cd command
to move around.

Use help to find out available commands.


Note: If you are running an older version of Micropython, you should update it. A lot of the functions used were introduced recently.
