<!--
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
-->


# Vagrant Usage


## How to use vagrant in a Linux environment

Clone EOxServer:

```sh
    git clone git@github.com:EOxServer/eoxserver.git
    cd eoxserver/
    git submodule init
    git submodule update
```

Install VirtualBox & Vagrant. The configuration is tested with:
* [Vagrant v1.3.5](http://downloads.vagrantup.com/tags/v1.3.5)
* [VirtualBox 4.3.0](https://www.virtualbox.org/wiki/Downloads)

Install Vagrant add-ons:
* `sahara` for [sandboxing](https://github.com/jedi4ever/sahara)
* `vagrant-vbguest` to [check for Virtualbox Guest Additions](https://github.com/dotless-de/vagrant-vbguest)
* `vagrant-cachier` to [cache yum/apt/etc. packages](https://github.com/fgrehm/vagrant-cachier)

```sh
    vagrant plugin install sahara
    vagrant plugin install vagrant-vbguest
    vagrant plugin install vagrant-cachier
```

Run vagrant:

```sh
    cd vagrant/
    vagrant up
```

EOxServer is now accessible at [http://localhost:8000/](http://localhost:8000/).

Run tests:

```sh
    vagrant ssh
    cd /var/eoxserver/autotest/
    export XML_CATALOG_FILES="../schemas/catalog.xml"
    python manage.py test autotest_services -v2
```

For further read and follow the autotest
[README](https://github.com/EOxServer/autotest).


## How to use vagrant in a Windows environment

Use the following steps:

1. Install git from http://git-scm.com/download/win
2. Install VirtualBox from
   http://download.virtualbox.org/virtualbox/4.3.2/VirtualBox-4.3.2-90405-Win.exe
3. Install vagrant from http://downloads.vagrantup.com/tags/v1.3.5 (use the .msi file)
4. Start a git bash and execute the following commands:

```sh
    git clone git@github.com:EOxServer/eoxserver.git
    cd eoxserver/
    git submodule init
    git submodule update
```

5. Open the Vagrantfile (located in ngeo-b/vagrant ) with an editor.
6. Add v.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "1"] before the line # Use GUI for debugging purposes
7. Save and close Vagrantfile
8. Open an Administrator Console (right click on the command prompt icon and select "Run as administrator")
9. Enter secpol.msc (and hit enter). Navigate to Local Policies, User Rights Assignment and check "Create symbolic links". Make sure that the Administrator account is added. Close it.
10. Still in the admin console enter: fsutil behavior set SymlinkEvaluation L2L:1 R2R:1 L2R:1 R2L:1 (and hit enter. This step isn't necessary on all systems. Only if you use net shares. But it does not hurt
11. Open the Administrative Tools Panel from the Control Panel. Open Component Services.
12. Select Computers, My Computer, Select DCOM Config.
13. Right click on "Virtual Box Application". Select Security. At "Launch and Activation Permissions" select Customize. Hit Edit.
14. Add your user account and Administrator. Select Permissions: Local Launch, Remote Launch, Local Activation and Remote Activation. Hit Ok. And again ok. Close the Component Services.
15. Log off and log on again.
16. Open an Administrator console and enter:

```sh
    vagrant plugin install sahara
    vagrant plugin install vagrant-vbguest
    vagrant plugin install vagrant-cachier
    cd vagrant/
    vagrant up
```

17. EOxServer is now accessible at [http://localhost:8000/](http://localhost:8000/).
18. Run tests:

```sh
    vagrant ssh
    cd /var/eoxserver/autotest/
    export XML_CATALOG_FILES="../schemas/catalog.xml"
    python manage.py test autotest_services -v2
```

19. For further read and follow the autotest [README](https://github.com/EOxServer/autotest).


## Troubleshoot vagrant

* If the provisioning didn't finish during vagrant up or after changes try: `vagrant provision`
* (Re-)Install virtualbox guest additions in case it complains about not matching versions: `vagrant vbguest -f`
* Slow performance: Check "Enable IO APIC", uncheck "Extended Features: Enable PAE/NX", and uncheck "Enable Nested Paging" in VirtualBox Manager.
* Symlinks with VirtualBox 4.1 not working: vi /opt/vagrant/embedded/gems/gems/vagrant-1.3.5/plugins/providers/virtualbox/driver/version_4_1.rb and add those changes: https://github.com/mitchellh/vagrant/commit/387692f9c8fa4031050646e2773b3d2d9b2c994e


# Build preparations

[Prepare a vagrant environment](https://gitlab.eox.at/vagrant/builder_rpm/tree/master).


## How to build EOxServer

# Check Jenkins build is passing.

```sh
    cd git/eoxserver/
    git pull

    # If starting a new release branch:
    git checkout -b 0.4
    vi eoxserver/__init__.py
    # Adjust version to future one
    git commit eoxserver/__init__.py -m "Adjusting version."
    git push origin 0.4

    vi eoxserver/__init__.py
    # Adjust version
    vi setup.py
    # Adjust Development Status
    git commit setup.py eoxserver/__init__.py -m "Adjusting version."
    # Info:
    #Development Status :: 1 - Planning
    #Development Status :: 2 - Pre-Alpha
    #Development Status :: 3 - Alpha
    #Development Status :: 4 - Beta
    #Development Status :: 5 - Production/Stable
    #Development Status :: 6 - Mature
    #Development Status :: 7 - Inactive

    git tag -a release-0.3.2 -m "Tagging the 0.3.2 release of EOxServer."
    git archive --format=tar --prefix=EOxServer-0.3.2/ release-0.3.2 | gzip > EOxServer-0.3.2.tar.gz
    mv EOxServer-0.3.2.tar.gz <path-to-builder_rpm>
    cd <path-to-builder_rpm>/
    vagrant ssh

    tar xzf EOxServer-0.3.2.tar.gz
    rm EOxServer-0.3.2.tar.gz
    cd EOxServer-0.3.2/

    # pypi
    python setup.py sdist
    #Check newly generated file dist/EOxServer-0.3.2.tar.gz
    python setup.py sdist upload
    # Administrate visible versions at pypi.python.org

    # rpm
    python setup.py bdist_rpm --release <NO>
    # Test packages in dist/

    cd dist/
    tar czf ../../rpmbuild/RPMS/EOxServer-0.3.2.tar.gz EOxServer-*rpm
    # scp EOxServer-0.3.2.tar.gz -> packages@packages.eox.at:.
    cd ../../
    rm -r EOxServer-0.3.2/

    vi eoxserver/__init__.py
    # Adjust version to dev
    vi setup.py
    # Adjust Development Status if necessary
    git commit setup.py eoxserver/__init__.py -m "Adjusting version."

    git push
    git push --tags
```

* Edit release at https://github.com/EOxServer/eoxserver/releases
* Edit milestones at https://github.com/EOxServer/eoxserver/issues/milestones
* Mail to dev & users
* Tweet
