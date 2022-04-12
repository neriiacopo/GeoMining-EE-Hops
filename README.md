# Geo Mining
![AA_ee_black_2](https://user-images.githubusercontent.com/50297074/151965110-faf885a2-d8ff-412b-ac33-0ac9422a9a40.jpg)

This repository collects a computational pipeline to mine geospatial data through Google Earth Engine in Grasshopper 3D, via its most recent Hops component.

## Requirements
- [Rhinoceros](https://www.rhino3d.com/download/) (7)
- [Python 3](https://www.python.org/downloads/) (=>3.7)

## REMOTE : using Flask-ngrok and Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/neriiacopo/GeoMining-EE-Hops/blob/backup_v1/GeoMining_EE_Hops.ipynb)

## LOCAL : to live connect to Earth Engine
## Installation
1. **[clone the repository](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)**
  - open a Terminal (mac) or run PowerShell (win)
  - change directory to your desidered path `example: cd /Users/xxx/Desktop/`
  - git clone https://github.com/neriiacopo/GeoMining-EE-Hops.git

2. **[virtual environment](https://docs.python.org/3/tutorial/venv.html)**
  - enter the repository `cd GeoMining-EE-Hops`
  - create the virtual environment `python -m venv env_GeoMining`
  - mac: `source /env_GeoMining/bin/activate`
  - win: `.\env_GeoMining\Scripts\activate`
3. **install dependencies**
  - `pip install -r requirements.txt`
4. **[authenticate to Earth Engine](https://developers.google.com/earth-engine/guides/python_install)**
  - Locally store your credentials to access Earth Engine `python hello_ee.py`

## Usage
- Change directory in the Terminal/PowerShell to repository folder
- Activate your virtual environment (as explained above)
- Connect Grasshopper to Earth Engine via Hops `python import_ee.py`

## Troubleshooting
- if `.\env_GeoMining\Scripts\activate` fails to run in Windows
  - make sure you run Powershell as Administrator 
  - `Set-ExecutionPolicy RemoteSigned`
  - `y`
  - `.\env_GeoMining\Scripts\activate`

- if any of the Python scripts fails to run 
  - check if you Python2 installed as well and make sure to call Python3
  - `python3 -m venv env_GeoMining`
  - `python3 hello_ee.py`
  - `python3 import_ee.py`
