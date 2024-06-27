#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 This file is part of OpenModelica.

 Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
 c/o Linköpings universitet, Department of Computer and Information Science,
 SE-58183 Linköping, Sweden.

 All rights reserved.

 THIS PROGRAM IS PROVIDED UNDER THE TERMS OF THE BSD NEW LICENSE OR THE
 GPL VERSION 3 LICENSE OR THE OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2.
 ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES
 RECIPIENT'S ACCEPTANCE OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3,
 ACCORDING TO RECIPIENTS CHOICE.

 The OpenModelica software and the OSMC (Open Source Modelica Consortium)
 Public License (OSMC-PL) are obtained from OSMC, either from the above
 address, from the URLs: http://www.openmodelica.org or
 http://www.ida.liu.se/projects/OpenModelica, and in the OpenModelica
 distribution. GNU version 3 is obtained from:
 http://www.gnu.org/copyleft/gpl.html. The New BSD License is obtained from:
 http://www.opensource.org/licenses/BSD-3-Clause.

 This program is distributed WITHOUT ANY WARRANTY; without even the implied
 warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE, EXCEPT AS
 EXPRESSLY SET FORTH IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE
 CONDITIONS OF OSMC-PL.

 Author : Adeel Asghar <adeel.asghar@liu.se>
"""

import os
import argparse
import re

def list_files(base_dir, exclude_files_dirs, f, recursive):
  # Compile regular expressions for exclusions
  exclude_files_dirs_regex = [re.compile(pattern) for pattern in exclude_files_dirs]

  for root, dirs, files in os.walk(base_dir):
    # Exclude specified directories
    dirs[:] = [d for d in dirs if not any(regex.match(d) for regex in exclude_files_dirs_regex)]
    reset_output_path = False
    if root != base_dir:
      nested_dir = root.replace(base_dir, '')
      nested_dir = nested_dir.replace('/','\\')
      reset_output_path = True
      f.write('strcpy $R0 $OUTDIR\n')
      f.write('${SetOutPath} "$R0' + nested_dir + '"\n')

    for file in files:
      if not any(regex.match(file) for regex in exclude_files_dirs_regex):
        file_path = os.path.join(root, file)
        file_path = file_path.replace('/','\\')
        f.write('${File} "' + file_path + '" "' + file + '"\n')

    if reset_output_path:
      reset_output_path = False
      # reset output but don't track it for uninstall
      f.write('SetOutPath "$R0"\n')

    if not recursive:
      break

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Generates a list of files to copy for NSIS installer.')
  parser.add_argument('--MSYSRUNTIME', type=str, default="ucrt", help='Specify MSYSRUNTIME either mingw or ucrt.')
  parser.add_argument('--PLATFORMVERSION', type=str, default="64", help='Specify PLATFORMVERSION either 32 or 64.')
  args = parser.parse_args()

  f = open("FilesList.nsh", "w")
  # Create bin directory and copy files in it
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\bin"' + '\n')
  base_directory = "..\\build\\bin"
  list_files(base_directory, [], f, False)
  f.write('${File} "..\OSMC-License.txt" "OSMC-License.txt"' + '\n')
  # Copy the openssl binaries
  if args.PLATFORMVERSION == "32":
    f.write('${File} "bin\\32bit\libeay32.dll" "libeay32.dll"' + '\n')
    f.write('${File} "bin\\32bit\libssl32.dll" "libssl32.dll"' + '\n')
    f.write('${File} "bin\\32bit\ssleay32.dll" "ssleay32.dll"' + '\n')
  else:
    f.write('${File} "bin\\64bit\libeay32.dll" "libeay32.dll"' + '\n')
    f.write('${File} "bin\\64bit\libssl-1_1-x64.dll" "libssl-1_1-x64.dll"' + '\n')
    f.write('${File} "bin\\64bit\ssleay32.dll" "ssleay32.dll"' + '\n')
  # Copy the qt plugins
  OMDEV = os.environ['OMDEV']
  OMDEV = OMDEV.replace('/', '\\')
  base_directory = OMDEV + "\\tools\msys\\" + args.MSYSRUNTIME + args.PLATFORMVERSION + "\share\qt5\plugins"
  files_dirs_to_exclude = [r"\*.svn"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  # Create the bin\osgPlugins-3.6.5 directory
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\bin\osgPlugins-3.6.5"' + '\n')
  base_directory = OMDEV + "\\tools\msys\\" + args.MSYSRUNTIME + args.PLATFORMVERSION + "\\bin\osgPlugins-3.6.5"
  files_dirs_to_exclude = [r"\*.svn"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  # Create bin\ffi directory and copy files in it
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\bin\\ffi"' + '\n')
  base_directory = "..\\build\\bin\\ffi"
  list_files(base_directory, [], f, False)
  # Create bin\omc-semla directory and copy files in it
  f.write('!if /FILEEXISTS "..\\build\\bin\omc-semla\*.*"' + '\n')
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\bin\omc-semla"' + '\n')
  base_directory = "..\\build\\bin\omc-semla"
  list_files(base_directory, [], f, True)
  f.write('!endif' + '\n')
  # Create icons directory and copy files in it
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\icons"' + '\n')
  base_directory = "icons"
  files_dirs_to_exclude = [r"\*.svn"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  f.write('${File} "..\OMEdit\OMEditLIB\Resources\icons\omedit.ico" "omedit.ico"' + '\n')
  f.write('${File} "..\OMOptim\OMOptim\GUI\Resources\omoptim.ico" "omoptim.ico"' + '\n')
  f.write('${File} "..\OMPlot\OMPlot\OMPlotGUI\Resources\icons\omplot.ico" "omplot.ico"' + '\n')
  f.write('${File} "..\OMShell\OMShell\OMShellGUI\Resources\omshell.ico" "omshell.ico"' + '\n')
  f.write('${File} "..\OMNotebook\OMNotebook\OMNotebookGUI\Resources\OMNotebook_icon.ico" "OMNotebook_icon.ico"' + '\n')
  # Create include\omc directory and copy files in it
  f.write('${AddItem} "\\\\?\\$INSTDIR\include"' + '\n')
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\include\omc"' + '\n')
  base_directory = "..\\build\include\omc"
  files_dirs_to_exclude = [r"\*.svn"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  # Create lib\omc directory and copy files in it
  f.write('${AddItem} "\\\\?\\$INSTDIR\lib"' + '\n')
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\lib\omc"' + '\n')
  base_directory = "..\\build\lib\omc"
  files_dirs_to_exclude = [r"\*.svn", r"\*.git"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  # Create lib\python directory and copy files in it
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\lib\python"' + '\n')
  base_directory = "..\\build\lib\python"
  files_dirs_to_exclude = [r"\*.svn", r"\*.git"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  # Create tools directory and copy files in it
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\tools"' + '\n')
  # copy the setup file / readme
  f.write('${File} "' + OMDEV + '\\tools\MSYS_SETUP.bat" "MSYS_SETUP.bat"' + '\n')
  f.write('${File} "' + OMDEV + '\\tools\MSYS_SETUP.txt" "MSYS_SETUP.txt"' + '\n')
  # Create msys directory and copy files in it
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\tools\msys"' + '\n')
  base_directory = OMDEV + "\\tools\msys"
  files_dirs_to_exclude = [r"group", r"passwd", r"pacman.log", r"tmp\.*\.*", r".*\.pyc", r"libQt5.*\.*", r"libQt6.*\.*"
                           , r"moc.exe", r"qt.*\.qch", r"Qt5.*\.*", r"qt5.*\.*", r"Qt6.*\.*", r"qt6.*\.*", r"libwx.*\.*", r"libgtk.*\.*", r"qtcreator", r"rcc.exe"
                           , r"testcon.exe", r"libsicu.*\.*", r"libicu.*\.*", r"wx.*\.dll", r"libosg.*\.*", r"Adwaita", r"OpenSceneGraph", r"gtk-doc"
                           , r"poppler", r"man", r"libdbus.*", r"tcl.*\.*", r"avcodec.*\.*", r"windeployqt.exe", r"python3.5", r"mingw_osg.*\.*"
                           , r"ActiveQt", r"Qt3DCore", r"Qt3DInput", r"Qt3DLogic", r"Qt3DQuick", r"Qt3DQuickInput"
                           , r"Qt3DQuickRender", r"Qt3DRender", r"QtBluetooth", r"QtCLucene", r"QtConcurrent", r"QtCore"
                           , r"QtDBus", r"QtDesigner", r"QtDesignerComponents", r"QtGui", r"QtHelp", r"QtLabsControls"
                           , r"QtLabsTemplates", r"QtLocation", r"QtMultimedia", r"QtMultimediaQuick_p", r"QtMultimediaWidgets"
                           , r"QtNetwork", r"QtNfc", r"QtOpenGL", r"QtOpenGLExtensions", r"QtPlatformHeaders", r"QtPlatformSupport"
                           , r"QtPositioning", r"QtPrintSupport", r"QtQml", r"QtQmlDevTools", r"QtQuick", r"QtQuickParticles"
                           , r"QtQuickTest", r"QtQuickWidgets", r"QtScript", r"QtScriptTools", r"QtSensors", r"QtSerialBus"
                           , r"QtSerialPort", r"QtSql", r"QtSvg", r"QtTest", r"QtUiPlugin", r"QtUiTools", r"QtWebChannel"
                           , r"QtWebKit", r"QtWebKitWidgets", r"QtWebSockets", r"QtWidgets", r"QtWinExtras", r"QtXml", r"QtXmlPatterns"
                           , r"osg", r"osgAnimation", r"osgDB", r"osgFX", r"osgGA", r"osgManipulator", r"osgParticle", r"osgPresentation"
                           , r"osgQt", r"osgShadow", r"osgSim", r"osgTerrain", r"osgText", r"osgUI", r"osgUtil", r"osgViewer"
                           , r"osgVolume", r"osgWidget", r"clang-cl.exe", r"clang-check.exe", r"llvm-lto2.exe", r"doc", r".gitignore"]
  if args.PLATFORMVERSION == "32":
    files_dirs_to_exclude = files_dirs_to_exclude + [r"mingw64", r"ucrt64", r"clang64"]
  else: # 64 bit
    if args.MSYSRUNTIME == "ucrt":
      files_dirs_to_exclude = files_dirs_to_exclude + [r"mingw32", r"mingw64", r"clang64", r"clang32"]
    else: # mingw64
      files_dirs_to_exclude = files_dirs_to_exclude + [r"mingw32", r"ucrt64", r"clang64", r"clang32"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  # Create share directory and copy files in it
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\share"' + '\n')
  base_directory = "..\\build\share"
  files_dirs_to_exclude = [r"\*.svn", r"\*.git"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  # Copy the OpenModelica web page & users guide url shortcut
  f.write('${AddItem} "\\\\?\\$INSTDIR\share\doc"' + '\n')
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\share\doc\omc"' + '\n')
  f.write('${File} "..\doc\OpenModelica Project Online.url" "OpenModelica Project Online.url"' + '\n')
  f.write('${File} "..\doc\OpenModelicaUsersGuide.url" "OpenModelicaUsersGuide.url"' + '\n')
  # Copy OMSens directory
  f.write('${SetOutPath} "\\\\?\\$INSTDIR\\share\OMSens"' + '\n')
  base_directory = "..\\build\share\OMSens"
  files_dirs_to_exclude = [r"\*.git"]
  list_files(base_directory, files_dirs_to_exclude, f, True)
  f.close
  print("Successfully generated file FilesList.nsh")
