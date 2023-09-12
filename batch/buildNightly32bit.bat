REM @echo off
REM @echo off & setlocal enableextensions
REM Task to automatically build the Windows nigthly-build for OpenModelica
REM Adrian.Pop@liu.se
REM 2012-10-08
REM last change: 2015-05-08

if not exist "c:\OMDev\" (
  echo Checkout c:\OMDev\
  cd C:\
  git clone https://openmodelica.org/git/OMDev.git OMDev
  cd C:\OMDev
  git checkout master
  call SETUP_OMDEV.bat
  call SETUP_OMDEV_Qt5.bat
  set OMDEV=C:\OMDev
)

if not exist "c:\dev\" (
  echo Creating c:\dev
  md c:\dev\
)

if not exist "c:\dev\OpenModelica_releases" (
 echo Creating c:\dev\OpenModelica_releases
 md c:\dev\OpenModelica_releases
)

if not exist "c:\dev\OM32bit\" (
  echo Checkout c:\dev\OM32bit
  cd c:\dev\
  git clone --recursive https://github.com/OpenModelica/OpenModelica.git OM32bit
  cd OM32bit
)

if not exist "c:\dev\OM32bit\OMSetup\" (
  echo Checkout c:\dev\OM32bit\OMSetup
  cd c:\dev\OM32bit\
  git clone https://github.com/OpenModelica/OpenModelicaSetup OMSetup
)

REM update the build script first!
cd c:\dev\OM32bit\OMSetup
git pull

REM update OMDev
cd C:\OMDev
git pull

REM run the Msys script to build the release
cd c:\dev\OpenModelica_releases\
set MSYSTEM=MINGW32
%OMDEV%\tools\msys\usr\bin\sh --login -i -c "time /c/dev/OM32bit/OMSetup/BuildWindowsRelease.sh adrpo -j3 32bit %1%"
