@ECHO OFF

SETLOCAL

REM Determine the version of installed Python3 (32-bit or 64-bit)
SET py3_list=33 34 35 36
SET py3_temp=%localappdata%\Programs\Python
SET py3_ver=32-32
SET py3_base=
SET py3_modules=%appdata%\Python

FOR %%v IN (%py3_list%) DO (
    IF EXIST %py3_temp%\Python%%v-32\python.exe (
        SET py3_base=%py3_temp%\Python%%v-32
        SET py3_ver=%%v-32
    )
)

FOR %%v IN (%py3_list%) DO (
    IF EXIST %py3_temp%\Python%%v\python.exe (
        SET py3_base=%py3_temp%\Python%%v
        SET py3_ver=%%v
    )
)

REM Chech if Python3 is installed
IF DEFINED py3_base (
    REM
) ELSE (
    @ECHO **** Python3 not found! Please install the latest versions of Python3. ****
    START "" https://www.python.org/downloads/
    EXIT /B 0
)

@ECHO **** Found installed Python3 (%py3_ver%) at %py3_base% ****

REM Check if s2m is installed
SET s2m=%py3_modules%\Python%py3_ver%\Scripts\s2m.exe
SET s2m_base=%py3_modules%\Python%py3_ver%\site-packages\s2m

SET uflash=%py3_modules%\Python%py3_ver%\Scripts\uflash.exe
SET s2m_mb=%py3_modules%\Python%py3_ver%\site-packages\s2m\micro_bit_scripts\s2mb_min.py

IF EXIST %s2m% (
    @ECHO **** Found installed s2m at %s2m% ****
) ELSE (
    @ECHO **** s2m not found! Install s2m and uflash from PyPI. ****
    %py3_base%\Scripts\pip.exe install --user --upgrade s2m==2.4
    %py3_base%\Scripts\pip.exe install --user --upgrade uflash
    
    @ECHO **** Upload the s2m program to your Micro:Bit ****
    %uflash% %s2m_mb%
)

REM Auto launch s2m and Scratch2
IF EXIST  "%ProgramFiles(x86)%\Scratch 2\Scratch 2.exe" (
    %s2m% -l tw -b %s2m_base% -s "%ProgramFiles(x86)%\Scratch 2\Scratch 2.exe"
)
ELSE (
    %s2m% -l tw -b %s2m_base% -s "%ProgramFiles%\Scratch 2\Scratch 2.exe"
)

ENDLOCAL
