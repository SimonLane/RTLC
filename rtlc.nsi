# ResponsiveTimelapseController for Windows installer script
# Requires Nullsoft Scriptable Install System 3.x (http://nsis.sourceforge.net/)
# S.Crouch@soton.ac.uk

OutFile "rtlc-setup.exe"

!include "MUI2.nsh"
#!include "LogicLib.nsh"
#!include "include\AdvReplaceInFile.nsh"

Name "RTLC"
!define MUI_PRODUCT "RTLC"
!define MUI_ICON "rtlc.ico"

# Set initial installation path:
# - In a 32-bit windows,
#	$PROGRAMFILES -> C:\Program Files 
# - In 64-bit windows,
# 	$PROGRAMFILES or $PROGRAMFILES32 -> C:\Program Files (x86)
#	$PROGRAMFILES64 -> C:\Program Files

#InstallDir "$PROGRAMFILES\${MUI_PRODUCT}"
#InstallDir "$PROGRAMFILES64\${MUI_PRODUCT}"
InstallDir "C:\${MUI_PRODUCT}"
   
!define MUI_PAGE_HEADER_TEXT "Responsive Timelapse Controller"
!define MUI_WELCOMEPAGE_TITLE "Responsive Timelapse Controller"
# TODO: add in description of the software below
!define MUI_WELCOMEPAGE_TEXT "Welcome to the RTLC installer $\r$\n $\r$\nThe Responsive Timelapse Controller (RTLC) is software that ...$\r$\n $\r$\n\
 This package will install RTLC on your system in the C:\RTLC directory"

!define MUI_WELCOMEFINISHPAGE_BITMAP ".\rtlc-welcome-finish.bmp"


!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
#!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

# TODO: add in appropriate URL and link text here
#!define MUI_FINISHPAGE_LINK "http://<add url text here>/"
#!define MUI_FINISHPAGE_LINK_LOCATION "http://<add url link here>/"

!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

# Required to write to Program Files / modify start menu
RequestExecutionLevel admin

# default section
Section "install"
	
	SetOutPath "$INSTDIR"
	File /r "dist"
	File /r "LICENSE.txt"
	File /r "rtlc.bat"
	File /r "rtlc.ico"
	File /r "vendor\Python27-pyqt-numpy-pil.zip"

	CreateDirectory "$INSTDIR\vendor"
	DetailPrint "Extracting prepackaged Python with dependent libraries (this may take a couple of minutes)..."
	nsisunz::Unzip "Python27-pyqt-numpy-pil.zip" "$INSTDIR\vendor"
	Delete "Python27-pyqt-numpy-pil.zip"
	
SectionEnd
	
# Start Menu Entries
Section	
	# RTLC
	createDirectory "$SMPROGRAMS\${MUI_PRODUCT}"	
	createShortCut "$SMPROGRAMS\${MUI_PRODUCT}\RTLC.lnk" "$INSTDIR\rtlc.bat" "" "$INSTDIR\rtlc.ico"
		
	# Uninstaller
	writeUninstaller "$INSTDIR\rtlc-uninstall.exe"
	createShortCut "$SMPROGRAMS\${MUI_PRODUCT}\Uninstall.lnk" '"$INSTDIR\rtlc-uninstall.exe"'
SectionEnd

Section "uninstall"
	
	# Clean up Start Menu
	delete "$SMPROGRAMS\${MUI_PRODUCT}\RTLC.lnk"
	delete "$SMPROGRAMS\${MUI_PRODUCT}\Uninstall.lnk"
	rmDir "$SMPROGRAMS\${MUI_PRODUCT}"
	
	# Remove files
	rmDir /r "$INSTDIR"
SectionEnd
