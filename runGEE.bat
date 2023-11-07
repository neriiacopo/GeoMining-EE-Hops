@echo off

REM Replace path with correct one
call .\env_GeoMining\Scripts\activate.bat
python import_ee.py
pause