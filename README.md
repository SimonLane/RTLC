Responsive Timelapse Controller (RTLC)
======================================

v0.1 Technology Preview

Overview
--------

The Responsive Timelapse Controller (RTLC) software interfaces
with the Leica TCS SP8 Confocal microscope using the Computer
Aided Microscopy (CAM) interface, and allows multi-position
timelapse imaging.

Prerequisites
-------------

- Leica TCS SP8 Confocal microscope
- Leica Computer Aided Microscopy (CAM) license
- Microsoft Windows 7

Package Description
-------------------

This application is written in Python v2.7 and makes use of
the PyQT, NumPy and Python Image Library packages. These are
installed along with its own Python 2.7 in the C:\RTLC
directory, as a standalone installation separate from any other
installations of these packages you may have.

The RTLC installer was created using the Nullsoft Installer System
(NSIS) v3.0b3.

You can find the source code for RTLC in the RTLC\dist
directory.

This software is distributed under the GNU General Public
License v3, a copy of which can be found in RTLC\LICENSE.txt.

The software can be obtained in either source code or installable
form.

Obtaining the source code
-------------------------

1. Create a RTLC directory in the C drive of the machine.
2. Clone the [RTLC repository](https://www.github.com/SimonLane/RTLC.git) 
   within that directory.
3. Unpack the C:\RTLC\vendor\Python27-pyqt-numpy-pil.zip file, ensuring that
   the pythonw.exe file can be found within the C:\RTLC\vendor\Python27
   directory, and not within a further subdirectory.
4. Run rtlc.bat from the C:\RTLC directory.

Installation through Installer
------------------------------

1. Download the [RTLC installer](http://bit.ly/RTLCinstaller).
2. Run the rtlc-setup-v0.1.exe installer and follow the
    instructions. RTLC will be installed to C:\RTLC.
3. Follow the instructions given in the methods paper
    to set up the microscope's software
4. Edit C:\RTLC\config.ini, inserting details for your
    microscope software configuration.
5. Run RTLC from the Windows Start Menu.

Other Notes
-----------

The following packages are distributed with this software:

- [Python 2.7](https://www.python.org/), distributed under the Python Software Foundation 
license v2
- [PyQT](https://wiki.python.org/moin/PyQt), distributed under the GNU General Public License v3
- [NumPy](http://www.numpy.org/), distributed under the BSD License
- [Python Image Library](http://www.pythonware.com/products/pil/), distributed under its own license

These licenses are available in the RTLC\third-party-licenses directory.

This product includes software written by Eric Young 
(eay@cryptsoft.com)
This product includes software written by Tim Hudson (tjh@cryptsoft.com)

Microscope image art used for installer and application icon files
created by MedicalWP[1] and used under Creative Commons Attribution 
4.0 International (CC-BY-4.0) license [2].

[1] http://www.iconarchive.com/artist/medicalwp.html
[2] http://creativecommons.org/licenses/by/4.0/

Contact
-------

Please email simon.lane -AT- soton.ac.uk if you wish to get in touch about
the software.

------------------------------------------------------------------
Copyright (C) University of Southampton, UK.
