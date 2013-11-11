#!/bin/sh -e

# Add your custom configuration below.

# Add alias
if ! grep -Fxq "alias l=\"ls -lah\"" /root/.bashrc ; then
    cat << EOF >> /root/.bashrc
alias l="ls -lah"
EOF
    cat << EOF >> /home/vagrant/.bashrc
alias l="ls -lah"
EOF
fi

# Install buildtools, etc.
yum install -y rpmdevtools rpm-build yum-utils man

if [ ! -f "/home/vagrant/.rpmmacros" ] || ! grep -Fxq "%__os_install_post %{nil}" /home/vagrant/.rpmmacros ; then
    echo "%__os_install_post %{nil}" >> /home/vagrant/.rpmmacros
fi
