Responsive Timelapse Controller (RTLC)
v0.1 Technology Preview

Overview
--------


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

The installer was created using the Nullsoft Installer System
(NSIS) v3.0b3.

Installation
------------

 1. Run the rtlc-setup-v0.1.exe installer and follow the
    instructions. RTLC will be installed to C:\RTLC.
 2. Follow the instructions given in the methods paper
    to set up the microscope's software
 3. Edit C:\RTLC\config.ini, inserting details for your
    microscope software configuration.
 4. Run RTLC from the Windows Start Menu.

Other Notes
-----------

The following packages are distributed with this software:
 - Python 2.7, distributed under the Python Software Foundation 
license v2
 - PyQT, distributed under the GNU General Public License v3
 - NumPy, distributed under the BSD License
 - Python Image Library, distributed under its own license
These licenses are available in the RTLC\third-party-licenses directory.

This product includes software written by Eric Young 
(eay@cryptsoft.com)
This product includes software written by Tim Hudson 
(tjh@cryptsoft.com)

Microscope image art used for installer and application icon files
created by MedicalWP[1] and used under Creative Commons Attribution 
4.0 International (CC-BY-4.0) license [2].

[1] http://www.iconarchive.com/artist/medicalwp.html
[2] http://creativecommons.org/licenses/by/4.0/

------------------------------------------------------------------
Copyright (C) 2016 Simon Lane, Centre for Biological Sciences,
University of Southampton, UK.
