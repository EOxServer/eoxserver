#!/bin/sh -e

# Disable SELinux
if ! [ `getenforce` == "Disabled" ] ; then
    setenforce 0
fi
if ! grep -Fxq "SELINUX=disabled" /etc/selinux/config ; then
    sed -e 's/^SELINUX=.*$/SELINUX=disabled/' -i /etc/selinux/config
fi
