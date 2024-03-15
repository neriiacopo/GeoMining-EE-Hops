@echo off

echo.
echo        _/_/_/  _/_/_/_/    _/_/    _/      _/  _/_/_/  _/      _/  _/_/_/  _/      _/    _/_/_/   
echo     _/        _/        _/    _/  _/_/  _/_/    _/    _/_/    _/    _/    _/_/    _/  _/          
echo    _/  _/_/  _/_/_/    _/    _/  _/  _/  _/    _/    _/  _/  _/    _/    _/  _/  _/  _/  _/_/     
echo   _/    _/  _/        _/    _/  _/      _/    _/    _/    _/_/    _/    _/    _/_/  _/    _/      
echo  _/    _/  _/        _/    _/  _/      _/    _/    _/    _/_/    _/    _/    _/_/  _/    _/      
echo   _/_/_/  _/_/_/_/    _/_/    _/      _/  _/_/_/  _/      _/  _/_/_/  _/      _/    _/_/_/       
echo.

REM replace the following with the correct path on your computer
call "C:\*\*\anaconda3\Scripts\activate" env_GeoMining
python import_ee.py
pause
