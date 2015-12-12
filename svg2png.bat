@echo off
set BASE=%~dp0
set S=%BASE%src\images\
set D=%BASE%share\uPyIDE\images\
set PROG="%ProgramFiles%\Inkscape\inkscape.exe"

for %%f in (%S%*.svg) DO (
	ECHO convert %%f to %D%%%~nf.png
	%PROG% -z %%f -e %D%%%~nf.png
)
pause
