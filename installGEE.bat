@echo off

echo.
echo        _/_/_/  _/_/_/_/    _/_/    _/      _/  _/_/_/  _/      _/  _/_/_/  _/      _/    _/_/_/   
echo     _/        _/        _/    _/  _/_/  _/_/    _/    _/_/    _/    _/    _/_/    _/  _/          
echo    _/  _/_/  _/_/_/    _/    _/  _/  _/  _/    _/    _/  _/  _/    _/    _/  _/  _/  _/  _/_/     
echo   _/    _/  _/        _/    _/  _/      _/    _/    _/    _/_/    _/    _/    _/_/  _/    _/      
echo  _/    _/  _/        _/    _/  _/      _/    _/    _/    _/_/    _/    _/    _/_/  _/    _/      
echo   _/_/_/  _/_/_/_/    _/_/    _/      _/  _/_/_/  _/      _/  _/_/_/  _/      _/    _/_/_/       
echo.

echo MAKING VIRTUAL ENVIRONMENT ......................................................................
python -m venv env_GeoMining
call .\env_GeoMining\Scripts\activate.bat

echo INSTALLING PAGKAGES .............................................................................
pip install -r requirements.txt -q

echo AUTHORIZING DEVICE ..............................................................................
python -c "import ee; ee.Authenticate(auth_mode='notebook')"

echo SETUP COMPLETED .................................................................................
pause

