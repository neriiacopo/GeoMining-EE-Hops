@echo off

REM replace the following with the correct path on your computer
call "C:\*\*\anaconda3\Scripts\activate" env_GeoMining
python import_ee.py
pause
