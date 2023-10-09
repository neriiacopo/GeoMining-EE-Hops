@echo off

REM Replace path with correct one
call "C:\*\*\anaconda3\Scripts\activate" env_GeoMining
python import_ee.py
pause