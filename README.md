upy-shell
=========

MicroPython shell

This is a very simple command line based shell for MicroPython.
It is based on a stripped down version of cmd, which can be found
here: https://github.com/micropython/micropython-lib/pull/4

I use it by copying cmd.py an shell.py to my sdcard and add the following
line to my 1:/boot.py file:
```python
sys.path.append('1:/')
```

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
