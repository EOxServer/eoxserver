#!/bin/sh -e

# Add your custom configuration below.

# Add alias
cat << EOF >> /root/.bashrc
alias l="ls -lah"
EOF
cat << EOF >> /home/vagrant/.bashrc
alias l="ls -lah"
EOF
