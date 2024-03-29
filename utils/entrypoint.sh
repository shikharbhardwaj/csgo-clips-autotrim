#!/bin/sh

set -e

# use specified user name or use `default` if not specified
MY_USERNAME="${MY_USERNAME:-default}"

# use specified group name or use the same user name also as the group name
MY_GROUP="${MY_GROUP:-${MY_USERNAME}}"

# use the specified UID for the user
MY_UID="${MY_UID:-1000}"

# use the specified GID for the user
MY_GID="${MY_GID:-${MY_UID}}"


# check to see if group exists; if not, create it
if grep -q -E "^${MY_GROUP}:" /etc/group > /dev/null 2>&1
then
  echo "INFO: Group exists; skipping creation"
else
  echo "INFO: Group doesn't exist; creating..."
  # create the group
  addgroup -gid "${MY_GID}" "${MY_GROUP}" || (echo "INFO: Group exists but with a different name; renaming..."; groupmod -g "${MY_GID}" -n "${MY_GROUP}" "$(awk -F ':' '{print $1":"$3}' < /etc/group | grep ":${MY_GID}$" | awk -F ":" '{print $1}')")
fi


# check to see if user exists; if not, create it
if id -u "${MY_USERNAME}" > /dev/null 2>&1
then
  echo "INFO: User exists; skipping creation"
else
  echo "INFO: User doesn't exist; creating..."
  # create the user
  adduser --uid "${MY_UID}" --ingroup "${MY_GROUP}" --home "/home/${MY_USERNAME}" --shell /bin/sh --disabled-password --gecos "" "${MY_USERNAME}"
fi

# make the directories needed to run my app
mkdir -p /opt/myapp

# change ownership of any directories needed to run my app as the proper UID/GID
chown -R "${MY_USERNAME}:${MY_GROUP}" "/opt/myapp"

# start myapp
echo "INFO: Running myapp as ${MY_USERNAME}:${MY_GROUP} (${MY_UID}:${MY_GID})"

# exec and run the actual process specified in the CMD of the Dockerfile (which gets passed as ${*})
exec gosu "${MY_USERNAME}" "${@}"