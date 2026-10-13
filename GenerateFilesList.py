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

def nsis_quote(path):
  """Escape a filesystem path/name so NSIS treats it as literal text.

  NSIS expands $ as a variable prefix and ends a quoted argument at ", so both
  have to be escaped: $ becomes $$ and " becomes $\\". The $ substitution runs
  first because the " replacement itself introduces a $.
  """
  return path.replace('$', '$$').replace('"', '$\\"')

def list_files(base_dir, exclude_dirs, exclude_files, f, recursive):
  # Compile regular expressions for exclusions
  exclude_dirs_regex = [re.compile(pattern) for pattern in exclude_dirs]
  exclude_files_regex = [re.compile(pattern) for pattern in exclude_files]

  for root, dirs, files in os.walk(base_dir):
    # Exclude specified directories
    dirs[:] = [d for d in dirs if not any(regex.match(d) for regex in exclude_dirs_regex)]
    reset_output_path = False
    if root != base_dir:
      # relpath so that a directory named like base_dir deeper in the tree is
      # not stripped out as well, which str.replace would do
      nested_dir = '\\' + os.path.relpath(root, base_dir).replace('/','\\')
      reset_output_path = True
      f.write('strcpy $R0 $OUTDIR\n')
      f.write('${SetOutPath} "$R0' + nsis_quote(nested_dir) + '"\n')

    for file in files:
      if not any(regex.fullmatch(file) for regex in exclude_files_regex):
        file_path = os.path.join(root, file)
        file_path = file_path.replace('/','\\')
        f.write('${File} "' + nsis_quote(file_path) + '" "' + nsis_quote(file) + '"\n')

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
  parser.add_argument('--OPENMODELICAHOME', type=str, default=r"..\build", help='Path to the OpenModelica build/install directory (e.g. a CMake install prefix).')
  parser.add_argument('--OPENMODELICASOURCEDIR', type=str, default="..", help='Path to the OpenModelica source directory.')
  args = parser.parse_args()

  f = open("FilesList.nsh", "w")
  # Create bin directory and copy files in it
  f.write(r'${SetOutPath} "\\?\$INSTDIR\bin"' + '\n')
  base_directory = args.OPENMODELICAHOME + r"\bin"
  files_to_exclude = [r".*\.git.*"]
  list_files(base_directory, [], files_to_exclude, f, True)
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\OSMC-License.txt" "OSMC-License.txt"' + '\n')
  # Copy the openssl binaries
  if args.PLATFORMVERSION == "32":
    f.write(r'${File} "bin\32bit\libeay32.dll" "libeay32.dll"' + '\n')
    f.write(r'${File} "bin\32bit\libssl32.dll" "libssl32.dll"' + '\n')
    f.write(r'${File} "bin\32bit\ssleay32.dll" "ssleay32.dll"' + '\n')
  else:
    f.write(r'${File} "bin\64bit\libeay32.dll" "libeay32.dll"' + '\n')
    f.write(r'${File} "bin\64bit\libssl-1_1-x64.dll" "libssl-1_1-x64.dll"' + '\n')
    f.write(r'${File} "bin\64bit\ssleay32.dll" "ssleay32.dll"' + '\n')
  # Create icons directory and copy files in it
  f.write(r'${SetOutPath} "\\?\$INSTDIR\icons"' + '\n')
  base_directory = "icons"
  files_to_exclude = [r".*\.git.*"]
  list_files(base_directory, [], files_to_exclude, f, True)
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\OMEdit\OMEditLIB\Resources\icons\omedit.ico" "omedit.ico"' + '\n')
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\OMOptim\OMOptim\GUI\Resources\omoptim.ico" "omoptim.ico"' + '\n')
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\OMPlot\OMPlot\OMPlotGUI\Resources\icons\omplot.ico" "omplot.ico"' + '\n')
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\OMShell\OMShell\OMShellGUI\Resources\omshell.ico" "omshell.ico"' + '\n')
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\OMNotebook\OMNotebook\OMNotebookGUI\Resources\OMNotebook_icon.ico" "OMNotebook_icon.ico"' + '\n')
  # Create include\omc directory and copy files in it
  f.write(r'${AddItem} "\\?\$INSTDIR\include"' + '\n')
  f.write(r'${SetOutPath} "\\?\$INSTDIR\include\omc"' + '\n')
  base_directory = args.OPENMODELICAHOME + r"\include\omc"
  files_to_exclude = [r".*\.git.*"]
  list_files(base_directory, [], files_to_exclude, f, True)
  # Create lib\omc directory and copy files in it
  f.write(r'${AddItem} "\\?\$INSTDIR\lib"' + '\n')
  f.write(r'${SetOutPath} "\\?\$INSTDIR\lib\omc"' + '\n')
  base_directory = args.OPENMODELICAHOME + r"\lib\omc"
  files_to_exclude = [r".*\.git.*"]
  list_files(base_directory, [], files_to_exclude, f, True)
  # Create tools directory and copy files in it
  f.write(r'${SetOutPath} "\\?\$INSTDIR\tools"' + '\n')
  # copy the setup file / readme
  OMDEV = os.environ['OMDEV']
  OMDEV = OMDEV.replace('/', '\\')
  f.write('${File} "' + OMDEV + r'\tools\MSYS_SETUP.bat" "MSYS_SETUP.bat"' + '\n')
  f.write('${File} "' + OMDEV + r'\tools\MSYS_SETUP.txt" "MSYS_SETUP.txt"' + '\n')
  # Create msys directory and copy files in it
  f.write(r'${SetOutPath} "\\?\$INSTDIR\tools\msys"' + '\n')
  base_directory = OMDEV + r"\tools\msys"
  dirs_to_exclude = [r"tmp", r"qtcreator", r"Adwaita", r"OpenSceneGraph", r"gtk-doc" , r"poppler", r"man"
                     , r"python3.5", r"ActiveQt", r"Qt3DCore", r"Qt3DInput", r"Qt3DLogic", r"Qt3DQuick"
                     , r"Qt3DQuickInput" , r"Qt3DQuickRender", r"Qt3DRender", r"QtBluetooth", r"QtCLucene", r"QtConcurrent"
                     , r"QtCore", r"QtDBus", r"QtDesigner", r"QtDesignerComponents", r"QtGui", r"QtHelp", r"QtLabsControls"
                     , r"QtLabsTemplates", r"QtLocation", r"QtMultimedia", r"QtMultimediaQuick_p", r"QtMultimediaWidgets"
                     , r"QtNetwork", r"QtNfc", r"QtOpenGL", r"QtOpenGLExtensions", r"QtPlatformHeaders", r"QtPlatformSupport"
                     , r"QtPositioning", r"QtPrintSupport", r"QtQml", r"QtQmlDevTools", r"QtQuick", r"QtQuickParticles"
                     , r"QtQuickTest", r"QtQuickWidgets", r"QtScript", r"QtScriptTools", r"QtSensors", r"QtSerialBus"
                     , r"QtSerialPort", r"QtSql", r"QtSvg", r"QtTest", r"QtUiPlugin", r"QtUiTools", r"QtWebChannel"
                     , r"QtWebKit", r"QtWebKitWidgets", r"QtWebSockets", r"QtWidgets", r"QtWinExtras", r"QtXml"
                     , r"QtXmlPatterns" , r"osg", r"osgAnimation", r"osgDB", r"osgFX", r"osgGA", r"osgManipulator"
                     , r"osgParticle" , r"osgPresentation", r"osgQt", r"osgShadow", r"osgSim", r"osgTerrain"
                     , r"osgText", r"osgUI", r"osgUtil", r"osgViewer", r"osgVolume", r"osgWidget", r"doc"]

  files_to_exclude = [r"group", r"passwd", r"pacman.log", r"libQt5.*\.*", r"libQt6.*\.*"
                      , r"moc.exe", r"qt.*\.qch", r"Qt5.*\.*", r"qt5.*\.*", r"Qt6.*\.*", r"qt6.*\.*", r"libwx.*\.*", r"libgtk.*\.*"
                      , r"rcc.exe", r"testcon.exe", r"libsicu.*\.*", r"libicu.*\.*", r"wx.*\.dll", r"libosg.*\.*", r"libdbus.*", r"tcl.*\.*", r"avcodec.*\.*"
                      , r"windeployqt.exe", r"mingw_osg.*\.*", r"clang-cl.exe", r"clang-check.exe", r"llvm-lto2.exe", r"\.gitignore", r"utf8_and_gbk.dll"]

  if args.PLATFORMVERSION == "32":
    dirs_to_exclude = dirs_to_exclude + [r"mingw64", r"ucrt64", r"clang64"]
  else: # 64 bit
    if args.MSYSRUNTIME == "ucrt":
      dirs_to_exclude = dirs_to_exclude + [r"mingw32", r"mingw64", r"clang64", r"clang32"]
    else: # mingw64
      dirs_to_exclude = dirs_to_exclude + [r"mingw32", r"ucrt64", r"clang64", r"clang32"]
  list_files(base_directory, dirs_to_exclude, files_to_exclude, f, True)
  # Create tmp folder for msys
  f.write(r'${SetOutPath} "\\?\$INSTDIR\tools\msys\tmp"' + '\n')
  # Create share directory and copy files in it
  f.write(r'${SetOutPath} "\\?\$INSTDIR\share"' + '\n')
  base_directory = args.OPENMODELICAHOME + r"\share"
  files_to_exclude = [r".*\.git.*"]
  list_files(base_directory, [], files_to_exclude, f, True)
  # Copy the OpenModelica web page & users guide url shortcut
  f.write(r'${AddItem} "\\?\$INSTDIR\share\doc"' + '\n')
  f.write(r'${SetOutPath} "\\?\$INSTDIR\share\doc\omc"' + '\n')
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\doc\OpenModelica Project Online.url" "OpenModelica Project Online.url"' + '\n')
  f.write('${File} "' + args.OPENMODELICASOURCEDIR + r'\doc\OpenModelicaUsersGuide.url" "OpenModelicaUsersGuide.url"' + '\n')
  # Copy OMSens directory
  f.write(r'${SetOutPath} "\\?\$INSTDIR\share\OMSens"' + '\n')
  base_directory = args.OPENMODELICAHOME + r"\share\OMSens"
  files_to_exclude = [r".*\.git.*"]
  list_files(base_directory, [], files_to_exclude, f, True)
  f.close()
  print("Successfully generated file FilesList.nsh")
