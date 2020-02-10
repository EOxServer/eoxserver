Installation
============

This document is a guide to install EOxServer.

Installing from packages
------------------------

EOxServer is packaged and distributed as a Python package.


Using Docker images
-------------------

If Docker is available, the easiest way to set up and use EOxServer
is to use the pre-built and maintained docker images. The images can
be obtained using the ``docker pull`` command like so:
::

    # docker pull eoxa/eoxserver
    Using default tag: latest
    latest: Pulling from eoxa/eoxserver
    93956c6f8d9e: Pull complete
    46bddb84d1c5: Pull complete
    15fa85048576: Pull complete
    8aa40341c4fa: Pull complete
    7a299ef02497: Pull complete
    09229f9ea579: Pull complete
    3163f1230278: Pull complete
    2f90ec943f31: Pull complete
    12b403f83389: Pull complete
    d6c5830b2cc6: Pull complete
    658ea0984fee: Pull complete
    7fbc330a1a79: Pull complete
    Digest: sha256:7ec2310bf28074c34410fadb72c2c1b7dddbd6e381d97ce22ce0d738cd591619
    Status: Downloaded newer image for eoxa/eoxserver:latest
    docker.io/eoxa/eoxserver:latest


.. note:: This will fetch the image with the ``latest`` tag by
          default. Other tags using a different operating system
          or package versions may be available as well.

This image can now be started using the ``docker run`` command.
::

    # docker run --rm -it -p 8000:8000 eoxa/eoxserver


As single docker containers are hard to control by themselves, other
tools like Docker Compose can help to keep static and runtime
configuration manageable.

Consider the following ``docker-compose.yml`` file:
::



