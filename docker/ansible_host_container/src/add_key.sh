#!/bin/bash

echo "Creating directory"
mkdir -p /home/ubuntu/.ssh

echo "Changing .ssh dir owner"
chown -R root /home/ubuntu/.ssh/

echo "Changing .ssh dir mode to 700"
chmod 700 /home/ubuntu/.ssh/

echo "Adding $1 file to .ssh/authorized_keys"
cat $1 >> /home/ubuntu/.ssh/authorized_keys

cat /home/ubuntu/.ssh/authorized_keys

echo "Setting sshd_config from $2"
cp $2 /etc/ssh/sshd_config

# echo "Changing auth file mode"
# chmod 600  ~/.ssh/authorized_keysd
