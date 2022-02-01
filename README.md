# AALU_Geo Mining
![AA_ee_black_2](https://user-images.githubusercontent.com/50297074/151965110-faf885a2-d8ff-412b-ac33-0ac9422a9a40.jpg)

This repository is produced for a masterclass at the Architectural Association Landscape Urbanism programme.

## Requirements
- [Rhinoceros](https://www.rhino3d.com/download/) (7)
- [Python 3](https://www.python.org/downloads/) (ideally 3.7 +)

## to run the Python script
## Installation
1. **[clone the repository](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)**
  - open a Terminal (mac) or run PowerShell (win)
  - change directory to your desidered path `example: cd /Users/xxx/Desktop/`
  - git clone https://github.com/neriiacopo/AALU-GeoMining.git

2. **[virtual environment](https://docs.python.org/3/tutorial/venv.html)**
  - with only Python3 installed `python -m venv env_GeoMining`
  - if Python2 and Python3 installed `python3 -m venv env_GeoMining`
  -  mac: `source /env_GeoMining/bin/activate`
  -  win: `.\env_GeoMining\Scripts\activate`
3. **install dependencies**
  - `pip install -r requirements.txt`
4. **authenticate to Earth Engine**
  - Run hello_ee.py to locally store your credentials to access EE

## Usage
- Change directory in the Terminal/PowerShell to repository folder
- Activate your virtual environment (as explained above)
- Run import_ee.py to connect Grasshopper to Google Earth via Hops

## Troubleshooting
- if `.\env_GeoMining\Scripts\activate` fails to run in Windows
  - make sure you run Powershell as Administrator 
  - `Set-ExecutionPolicy RemoteSigned`
  - `y`
  - `.\env_GeoMining\Scripts\activate`

