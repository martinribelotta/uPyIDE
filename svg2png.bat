@echo off
set BASE=%~dp0
set P=%BASE%share\uPyIDE\images
set PROG="%ProgramFiles%\Inkscape\inkscape.exe"

for %%f in (%P%\*.svg) DO ( %PROG% -z %%f -e %%~dpnf.png )
pause

