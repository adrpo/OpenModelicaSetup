#!/bin/sh
# Prepares an OpenModelica checkout for the encryption-enabled Windows release build
# (BuildWindowsRelease.sh with OM_ENABLE_ENCRYPTION=yes): clones or updates OMEncryption next to
# the OpenModelica sources, copies the public tool key into SEMLA and decrypts the private keys.
#
# usage: PrepareEncryption.sh <OpenModelica checkout, e.g. /c/dev/e/OM64bit>
#
# Expects C:\OMEncryptionNeeds\OMPublicKey (a git checkout holding public_key_tool.pem).
# The passphrase of the private keys is taken from OM_ENCRYPTION_KEY_PW when set (the Jenkins
# job binds it from a credential), otherwise from C:\OMEncryptionNeeds\pass-gpg-key.txt.
# Not run with -x: the passphrase must not end up in the log.

OM_DIR=$1
NEEDS=/c/OMEncryptionNeeds
if [ -z "${OM_DIR}" ] || [ ! -d "${OM_DIR}" ]; then
  echo "ERROR: usage: $0 <OpenModelica checkout>"
  exit 1
fi

set -e

if [ ! -d "${OM_DIR}/OMEncryption" ]; then
  echo "Checkout ${OM_DIR}/OMEncryption"
  git clone https://github.com/OpenModelica/OMEncryption "${OM_DIR}/OMEncryption"
fi

echo "Updating ${NEEDS}/OMPublicKey"
git -C "${NEEDS}/OMPublicKey" pull
echo "Updating ${OM_DIR}/OMEncryption"
git -C "${OM_DIR}/OMEncryption" pull

KEYS="${OM_DIR}/OMEncryption/3rdParty/SEMLA/src/openssl_keys"
cp "${NEEDS}/OMPublicKey/public_key_tool.pem" "${KEYS}/"

decrypt() {
  rm -f "${KEYS}/$1"
  OK=yes
  if [ -n "${OM_ENCRYPTION_KEY_PW}" ]; then
    printf '%s\n' "${OM_ENCRYPTION_KEY_PW}" | gpg --batch --passphrase-fd 0 -d "${KEYS}/$1.gpg" > "${KEYS}/$1" || OK=""
  else
    gpg --batch --passphrase-fd 0 -d "${KEYS}/$1.gpg" < "${NEEDS}/pass-gpg-key.txt" > "${KEYS}/$1" || OK=""
  fi
  # the redirection creates the file even when gpg fails
  if [ -z "${OK}" ] || [ ! -s "${KEYS}/$1" ]; then
    echo "ERROR: decryption of $1 failed"
    rm -f "${KEYS}/$1"
    exit 1
  fi
  echo "Decrypted $1"
}
decrypt private_key_lve.pem
decrypt private_key_tool.pem
