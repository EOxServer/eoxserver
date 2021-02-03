# Start EOXServer using docker

Install [docker](https://www.docker.com/) for your system.

The next steps are:

```sh
git clone git@github.com:EOxServer/eoxserver.git
cd eoxserver/
docker build -t eoxserver -f ./docker/<OS>/<py_version>/Dockerfile .
```
where `OS` and `py_version` are folders in the `docker` folder.

This will give you a docker image ID as the last output e.g `55453fbf21c9`. The
image ID can also be retrieved using the `docker images` command. The last image
you built should be at the top of the list.

**Note**: If you want to include static files for debugging create a debug_static.sh script:

debug_static.sh
```bash
#!/bin/bash

echo "Running debug_static.sh!"
cp /opt/scripts/urls.py /opt/instance/instance
```

and add the following line to be executed as a startup script to the sample.env:
```env
STARTUP_SCRIPTS=/opt/scripts/debug_static.sh
```

To run the image with static files do:

```sh
mkdir docker/scripts
cp autotest/autotest/urls.py docker/scripts
mv debug_static.sh docker/scripts
docker run -it --rm -p 8080:8000 --mount type=bind,source=$PWD/docker/scripts,target=/opt/scripts --env-file docker/sample.env <IMAGE_ID>
```

where `<IMAGE_ID>` is the image ID from before e.g. `55453fbf21c9`

The first few unique characters also work:

```sh
docker run -i -t --rm -p 8080:8000 5545
```

EOxServer is now accessible at [http://localhost:8080/](http://localhost:8080/).
And you can login to the `Admin Client` using:
- username: admin
- password: admin
