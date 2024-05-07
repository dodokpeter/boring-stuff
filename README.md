# BoringStuff
My **python** scripts to ease my life. 

## Set up
### Configuration
if needed, copy file BoringStuff.ini from root of the project to the user HOME directory.

### Python 
Python should be installed and configured. I prefer to use Anaconda3 for Python setup, which you can download from https://www.anaconda.com/products/individual
Necessary packages, that need to be installed into python:
- pyyaml   '''pip install pyyaml''' - editing and readin yaml files, in Anaconda3 it's preinstalled

### First run
When you are about to start using boring stuff scripts, Please run this command from directory, where you've cloned this project:
```
first.bat
```
If you want to check if everything works fine, just type in command line.
Run command
```
hello
```
to ensure that scrips can be run from CMD. 
  
  
<a href="./scripts/README.md">Available commands</a>

### Documentation notes
Each folder contains readme file for description of available scripts

### Dependencies:
#### Python libraries

**openpyxl** - working with excel files (Anaconda contains this lib)

#### Python libraries over conda command line

**pypdf2** - working with PDF files
```
conda install -c conda-forge pypdf2 
```
**python-docx** - working with .docx files
```
conda install -c conda-forge python-docx 
```
**pillow**

I had this same problem from . import _imaging as core ImportError: DLL load failed: The specified procedure could not be found. recently with Anaconda Navigator 1.6.12 running Python 3.6.4. I was loading PIL 4.3.0. Upgrading PIL to 5.0.0 via Anaconda Navigator did not fix it. I ultimately fixed it via the following two step procedure. 

1. Uninstall it via 
```conda remove --force pillow ```

2. Reinstall. Fearing something was wrong with the original Anaconda distribution, I reinstalled from conda-forge instead of conda's default. So I used 
```
conda install -c conda-forge pillow
```
NOTE: not working still: ImportError: DLL load failed: The specified module could not be found.

Next step was:
```
conda uninstall pillow
conda install pillow=5.0.0
```
This works.


**pytube3**

I run the command in anaconda terminal
```
conda install -c conda-forge youtube-dl
```
**MoviePy**

Installation command
```
conda install -c conda-forge moviepy
```

#### Selenium

 **- geckodriver for Selenium**
 
selenium.common.exceptions.WebDriverException: Message: 'geckodriver' executable needs to be in PATH.

First of all you will need to download latest executable geckodriver from 
https://github.com/mozilla/geckodriver/releases
to run latest firefox using selenium

Actually The Selenium client bindings tries to locate the geckodriver executable from the system PATH. You will need to add the directory containing the executable to the system path.

On Unix systems you can do the following to append it to your system’s search path, if you’re using a bash-compatible shell:
```
export PATH=$PATH:/path/to/directory/of/executable/downloaded/in/previous/step
```
On Windows you will need to update the Path system variable to add the full directory path to the executable geckodriver manually or command line(don't forget to restart your system after adding executable geckodriver into system PATH to take effect). The principle is the same as on Unix.


embedable for win, then:
$ curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
$ python get-pip.py