<<<<<<< HEAD
@echo off

echo.
echo        _/_/_/  _/_/_/_/    _/_/    _/      _/  _/_/_/  _/      _/  _/_/_/  _/      _/    _/_/_/   
echo     _/        _/        _/    _/  _/_/  _/_/    _/    _/_/    _/    _/    _/_/    _/  _/          
echo    _/  _/_/  _/_/_/    _/    _/  _/  _/  _/    _/    _/  _/  _/    _/    _/  _/  _/  _/  _/_/     
echo   _/    _/  _/        _/    _/  _/      _/    _/    _/    _/_/    _/    _/    _/_/  _/    _/      
echo  _/    _/  _/        _/    _/  _/      _/    _/    _/    _/_/    _/    _/    _/_/  _/    _/      
echo   _/_/_/  _/_/_/_/    _/_/    _/      _/  _/_/_/  _/      _/  _/_/_/  _/      _/    _/_/_/       
echo.

echo ACTIVATE VIRTUAL ENVIRONMENT ....................................................................
call .\env_GeoMining\Scripts\activate.bat

echo RUN APP .........................................................................................
python import_ee.py

pause
=======
@echo off

call .\env_GeoMining\Scripts\activate.bat
python import_ee.py
pause
>>>>>>> fa9f2e38128d7cd93029f3ba1523f090c07b862d
