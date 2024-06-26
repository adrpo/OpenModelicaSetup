#!/bin/sh -x
# script to build the OpenModelica nightly-build
# Adrian Pop [adrian.pop@liu.se]
# 2013-10-03
#
# expects to have these things installed:
#  nsis installer
#  TortoiseSVN command line tools
#  jdk
#  git command line clients (PUT IT LAST IN THE PATH!) http://git-scm.com/downloads
#  OMDev in c:\OMDev
#

# get the ssh password via command line
export SSHUSER=$1
export MAKETHREADS=$2
export PLATFORM=$3 # 32bit or 64bit
export GIT_TAG=$4
export OPENMODELICA_BRANCH=$GIT_TAG

# to build with encryption set OM_ENABLE_ENCRYPTION=yes
if [ "${OM_ENABLE_ENCRYPTION}" = "yes" ]; then
 export OM_ENCRYPT="e/"
 export OM_ENCRYPT_SUFFIX="-encryption"
 export OM_ENCRYPT_FLAGS="OM_ENABLE_ENCRYPTION=yes"
fi

# set the path to our tools
export PATH=$PATH:/c/Program\ Files/TortoiseSVN/bin/:/c/bin/jdk/bin:/c/bin/nsis3.04/:/c/bin/git/bin

# is this a PR build?
PR_BUILD=""
PR_NAME=""

XPREFIX="x64"
if [ "${PLATFORM}" = "32bit" ]; then
	XPREFIX="x86"
fi

MSYSRUNTIME=""
if [ "${MSYSTEM}" = "UCRT64" ]; then
	MSYSRUNTIME="ucrt"
fi
if [ "${MSYSTEM}" = "MINGW64" ]; then
	MSYSRUNTIME="mingw"
fi
if [ "${MSYSTEM}" = "MINGW32" ]; then
	MSYSRUNTIME="mingw"
fi


SIGNTOOL=`find /c/Program\ Files\ \(x86\)/Windows\ Kits/10/ -wholename "*${XPREFIX}/signtool.exe" | tail -1`
if [ "${SIGNTOOL}" = "" ]; then
 echo "Could not find signtool.exe"
 exit 1
fi

# don't exit on error
set +e
# make sure we use the windows temp directory and not the msys/tmp one!

# !!!!! make sure we don't do rm -f /* 
if [ ! -z "${TMP}" ]; then
 rm -rf ${TMP}/*
fi
if [ ! -z "${TEMP}" ]; then
 rm -rf ${TEMP}/*
fi
# of course msys2 changed the way one accesses the windows %TMP% and %TEMP% in sh
if [ ! -z "${ORIGINAL_TMP}" ]; then
export TMP=$ORIGINAL_TMP
fi
if [ ! -z "${ORIGINAL_TEMP}" ]; then
export TEMP=$ORIGINAL_TEMP
fi
if [ ! -z "${TMP}" ]; then
 rm -rf ${TMP}/*
fi
if [ ! -z "${TEMP}" ]; then
 rm -rf ${TEMP}/*
fi

# set the OPENMODELICAHOME and OPENMODELICALIBRARY
export OPENMODELICAHOME="c:/dev/${OM_ENCRYPT}OM${PLATFORM}/build"
export OPENMODELICALIBRARY="c:/dev/${OM_ENCRYPT}OM${PLATFORM}/build/lib/omlibrary"

export OMDEVWIN=${OMDEV}
export OMDEVMSYS=`cygpath -u ${OMDEV}`

# have OMDEV in Msys version
export OMDEV=${OMDEVMSYS}

# update OMDev
cd ${OMDEVMSYS}
git pull

# update OpenModelica
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}
# if we build an experimental PR number skip this!
if [[ "$OPENMODELICA_BRANCH" =~ PR_.*_experimental ]]; then
  echo "Building experimental PR build: $OPENMODELICA_BRANCH!"
  export PR_NAME=_${OPENMODELICA_BRANCH}
  export PR_BUILD="PRbuilds/"
else
  echo "Building $OPENMODELICA_BRANCH!"
  git fetch && git fetch --tags
  # attempt to reset to origin
  git checkout "$OPENMODELICA_BRANCH" && git reset --hard "origin/$OPENMODELICA_BRANCH" || true
  git reset --hard "$OPENMODELICA_BRANCH" && git checkout "$OPENMODELICA_BRANCH" && git submodule update --force --init --recursive && git pull --recurse-submodules && git fetch && git fetch --tags || exit 1
fi
git checkout -f "$OPENMODELICA_BRANCH" || exit 1
git reset --hard "$OPENMODELICA_BRANCH" || exit 1
git submodule update --force --init --recursive || exit 1

# get the revision
export REVISION=`git describe --match "v*.*" --always`${PR_NAME}
export REVISION_SHORT=`git describe --match "v*.*" --always --abbrev=0`
# remove the starting v from the string
REVISION_SHORT="${REVISION_SHORT:1}"
export PRODUCT_VERSION=${REVISION_SHORT}
# strip the string after "-" to get just the version number
BEGIN=${PRODUCT_VERSION/-*/}
PRODUCT_VERSION=${PRODUCT_VERSION::${#BEGIN}}
# make a valid VIProductVersion
PRODUCT_VERSION=${PRODUCT_VERSION}.0

# Directory prefix
export OMC_INSTALL_PREFIX="/c/dev/OpenModelica_releases/${OM_ENCRYPT}${REVISION}/"
# file suffix
export OMC_FILE_PREFIX="OpenModelica-${REVISION}-${PLATFORM}${OM_ENCRYPT_SUFFIX}"
# make the file prefix
export OMC_INSTALL_FILE_PREFIX="${OMC_INSTALL_PREFIX}${OMC_FILE_PREFIX}"

# test if exists and exit if it does
if [ -f "${OMC_INSTALL_FILE_PREFIX}.exe" ]; then

echo "Revision ${OMC_INSTALL_FILE_PREFIX}.exe already exists! Check the server ..."

else

# clean
rm -rf /c/dev/OpenModelica_releases/${OM_ENCRYPT}/v*
rm -rf build
git submodule foreach --recursive  "git fetch --tags && git reset --hard && git clean -fdxq -e /git -e /svn" || exit 1
git clean -fdxq -e OMSetup || exit 1
git status
git submodule status --recursive

# create the revision directory
mkdir -p ${OMC_INSTALL_PREFIX}

# update OpenModelicaSetup
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}/OMSetup
git checkout master
git pull

# build OpenModelica
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}
echo "Cleaning OpenModelica"
rm -rf build/
mkdir -p build/
make -f 'Makefile.omdev.mingw' ${MAKETHREADS} gitclean || make -f 'Makefile.omdev.mingw' ${MAKETHREADS} gitclean || true
make -f 'Makefile.omdev.mingw' ${MAKETHREADS} clean
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}

echo "Building OpenModelica and OpenModelica libraries"
# make sure we break on error!
set -e
make -f 'Makefile.omdev.mingw' ${MAKETHREADS} ${OM_ENCRYPT_FLAGS} omc omc-diff omlibrary qtclients
echo "Building CPP runtime"
make -f 'Makefile.omdev.mingw' ${MAKETHREADS} BUILDTYPE=Release runtimeCPPinstall
echo "Copying OMSens"
make -f 'Makefile.omdev.mingw' ${MAKETHREADS} omsens
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}
echo "Installing Python scripting"
rm -rf OMPython
git clone https://github.com/OpenModelica/OMPython -q -b master /c/dev/${OM_ENCRYPT}OM${PLATFORM}/OMPython
# build OMPython, don't fail for now until we can fix the UCRT build
make -k -f 'Makefile.omdev.mingw' ${MAKETHREADS} install-python || true

echo "OMJava scripting"
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}
rm -rf OMJava
git clone https://github.com/OpenModelica/OMJava.git
cd OMJava && make dep && make install
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}

# wget the html & pdf versions of OpenModelica users guide
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}/build/share/doc/omc
wget --no-check-certificate https://openmodelica.org/doc/openmodelica-doc-latest.tar.xz
tar -xJf openmodelica-doc-latest.tar.xz --strip-components=2
rm openmodelica-doc-latest.tar.xz
wget --no-check-certificate https://openmodelica.org/doc/OpenModelicaUsersGuide/OpenModelicaUsersGuide-latest.pdf
#cp OpenModelicaUsersGuide-latest.pdf OpenModelicaUsersGuide-latest.pdf

# get PySimulator
# for now get the master from github since OpenModelica plugin is still not part of tagged release. This should be updated once PySimulator outs a new release.
git clone https://github.com/PySimulator/PySimulator -q -b master /c/dev/${OM_ENCRYPT}OM${PLATFORM}/build/share/omc/scripts/PythonInterface/PySimulator

# get Figaro - let's not do that for now as it has log4j inside
#cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}/build/share
# do not get it from sourceforge as it fails sometimes!
#wget --no-check-certificate -O jEdit4.5_VisualFigaro.zip https://sourceforge.net/p/visualfigaro/code/HEAD/tree/Trunk/Package/4_Packages_livrables/jEdit4.5_VisualFigaro.zip?format=raw
#wget --no-check-certificate -O jEdit4.5_VisualFigaro.zip https://build.openmodelica.org/omc/figaro/v1.12/jEdit4.5_VisualFigaro.zip
#unzip jEdit4.5_VisualFigaro.zip
#rm jEdit4.5_VisualFigaro.zip

# OMSimulator
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}/
make -f Makefile.omdev.mingw omsimulator

# build the installer
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}/OMSetup
rm -rf 	OMLibraries.nsh
# generate the list of files for the installer
python GenerateFilesList.py --MSYSRUNTIME="${MSYSRUNTIME}" --PLATFORMVERSION="${PLATFORM::-3}"
# make sure we have it in Windows version for the NSIS
export OMDEV=${OMDEVWIN}
if ! makensis //DMSYSRUNTIME="${MSYSRUNTIME}" //DPLATFORMVERSION="${PLATFORM::-3}" //DOMVERSION="${REVISION_SHORT}" //DPRODUCTVERSION=${PRODUCT_VERSION} OpenModelicaSetup.nsi > trace.txt 2>&1 ; then
  cat trace.txt
  exit 1
fi

# sign the installer but do not fail!
"${SIGNTOOL}" sign //n "Open Source Modelica Consortium" //tr "http://timestamp.globalsign.com/tsa/r6advanced1" //a //td SHA256 //v OpenModelica.exe

# move the installer
mv OpenModelica.exe ${OMC_INSTALL_FILE_PREFIX}.exe

# gather the svn log
cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}
git log --name-status --graph --submodule > ${OMC_INSTALL_FILE_PREFIX}-ChangeLog.txt

# make the readme
export DATESTR=`date +"%Y-%m-%d_%H-%M"`
echo "Automatic build of OpenModelica by *.openmodelica.org at date: ${DATESTR} from revision: ${REVISION}" >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo " " >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo "Read OpenModelica-${REVISION}-ChangeLog.txt for more info on changes." >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo " " >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo "See also (match revision ${REVISION} to build jobs):" >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo "  https://test.openmodelica.org/hudson/" >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo "  http://test.openmodelica.org/~marsj/MSL32/BuildModelRecursive.html" >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo " " >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
cat >> ${OMC_INSTALL_FILE_PREFIX}-README.txt <<DELIMITER
*Instructions to prepare test information if you find a bug:*

generate a .mos script file loading all libraries and files your model need call simulate.
// start .mos script
loadModel(Modelica);
loadFile("yourfile.mo");
simulate(YourModel);
// end .mos script

Start this .mos script in a shell with omc and use the debug flags
+d=dumpdaelow,optdaedump,bltdump,dumpindxdae,backenddaeinfo.
Redirect the output stream in file ( > log.txt)

A series of commands to run via cmd.exe
is given below. Note that z: is the drive
where your .mos script is:
c:\> z:
z:\> cd \path\to\script(.mos)\file\
z:\path\to\script(.mos)\file\> \path\to\OpenModelica\bin\omc.exe
+d=dumpdaelow,optdaedump,bltdump,dumpindxdae,backenddaeinfo
YourScriptFile.mos > log.txt 2>&1

Either send the log.txt file alongwith your bug
description to OpenModelica@ida.liu.se or file a
bug in our bug tracker:
  https://trac.openmodelica.org/OpenModelica

Happy testing!
DELIMITER
echo " " >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo "Read more about OpenModelica at https://openmodelica.org" >> ${OMC_INSTALL_FILE_PREFIX}-README.txt
echo "Contact us at OpenModelica@ida.liu.se for further issues or questions." >> ${OMC_INSTALL_FILE_PREFIX}-README.txt

# make the testsuite-trace
#cd /c/dev/${OM_ENCRYPT}OM${PLATFORM}
#echo "Running testsuite trace"
#make -f 'Makefile.omdev.mingw' ${MAKETHREADS} testlogwindows > tmpTime.log 2>&1

echo "Check Jenkins testserver for the testsuite trace here (match revision ${REVISION} to build jobs): " >> ${OMC_INSTALL_FILE_PREFIX}-testsuite-trace.txt
echo "  https://test.openmodelica.org/jenkins/" >> ${OMC_INSTALL_FILE_PREFIX}-testsuite-trace.txt
echo "  https://test.openmodelica.org/jenkins/job/OM_Win/lastBuild/console" >> ${OMC_INSTALL_FILE_PREFIX}-testsuite-trace.txt
#cat tmpTime.log >> ${OMC_INSTALL_FILE_PREFIX}-testsuite-trace.txt
#rm -f tmpTime.log

fi # end checking for if [ -f "${OMC_INSTALL_FILE_PREFIX}.exe" ]; then

ls -lah ${OMC_INSTALL_PREFIX}

cd ${OMC_INSTALL_PREFIX}

FILE_PATH=/var/www/build.openmodelica.org/omc/builds/windows/nightly-builds/${PR_BUILD}${OM_ENCRYPT}${PLATFORM}/${OMC_FILE_PREFIX}.exe

# check if already on the server

SHOULD_COPY=false
ssh -i $HOME/.ssh/id_rsa -o UserKnownHostsFile=$HOME/.ssh/known_hosts -q ${SSHUSER}@build.openmodelica.org [[ -f $FILE_PATH ]] && SHOULD_COPY=false || SHOULD_COPY=true

if [ "${SHOULD_COPY}" = true ]; then

# move the last nightly build to the older location
ssh -i $HOME/.ssh/id_rsa -o UserKnownHostsFile=$HOME/.ssh/known_hosts ${SSHUSER}@build.openmodelica.org <<ENDSSH
#commands to run on remote host
cd /var/www/build.openmodelica.org/omc/builds/windows/nightly-builds/${PR_BUILD}${OM_ENCRYPT}${PLATFORM}/
#rm -f older/*.* || true
mv -f OpenModelica* older/ || true
ENDSSH
scp  -i $HOME/.ssh/id_rsa -o UserKnownHostsFile=$HOME/.ssh/known_hosts OpenModelica*${PLATFORM}* ${SSHUSER}@build.openmodelica.org:/var/www/build.openmodelica.org/omc/builds/windows/nightly-builds/${PR_BUILD}${OM_ENCRYPT}${PLATFORM}/
ssh  -i $HOME/.ssh/id_rsa -o UserKnownHostsFile=$HOME/.ssh/known_hosts ${SSHUSER}@build.openmodelica.org <<ENDSSH
#commands to run on remote host
cd /var/www/build.openmodelica.org/omc/builds/windows/nightly-builds/${PR_BUILD}${OM_ENCRYPT}${PLATFORM}/
pwd
echo "ln -s ${OMC_FILE_PREFIX}.exe OpenModelica-latest.exe"
ln -s ${OMC_FILE_PREFIX}.exe OpenModelica-latest.exe
ls -lah
echo "md5sum OpenModelica-latest.exe | cut -f 1 -d ' ' > OpenModelica-latest.exe.md5sum"
md5sum OpenModelica-latest.exe | cut -f 1 -d ' ' > OpenModelica-latest.exe.md5sum
cp OpenModelica-latest.exe.md5sum ${OMC_FILE_PREFIX}.exe.md5sum
cat OpenModelica-latest.exe.md5sum
ls -lah
ENDSSH

fi # if [ "${SHOULD_COPY}" = true ]; then

echo "All done!"
