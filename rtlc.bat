@echo off
set RTLCHOME=C:\RTLC
set RTLCDIST=%RTLCHOME%\dist
set PYTHONHOME=%RTLCHOME%\vendor\Python27
set PATH=%PYTHONHOME%;%PATH%

cd %RTLCDIST%
python.exe LeicaDriver5.py