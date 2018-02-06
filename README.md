mdqc
====

A cross-platform tool designed to expedite metadata quality control across large numbers of digital assets.

For binaries and more information, please refer to [our website](http://www.avpreserve.com/avpsresources/tools/)

MacOS Build

- pip install -U py2app
- python setup.py py2app
- find the app in mdqc/osx/dist/MDQC.app


Windows Build

- install pip
- [install pyinstaller](https://pythonhosted.org/PyInstaller/installation.html)
- Update path in the [MDQC.spec](https://github.com/avpreserve/mdqc/blob/master/win/MDQC.spec) file for windows version 
- Run following command to generate MDQC.exe file

 > pyinstaller.exe -w -F -n MDQC.exe --clean MDQC.spec