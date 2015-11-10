# Start EOXServer using docker

Install [docker](https://www.docker.com/) for your system.

The next steps are:

```sh
git clone git@github.com:EOxServer/eoxserver.git
cd eoxserver/
docker build docker
```

This will give you a docker image ID as the last output e.g `55453fbf21c9`. The
image ID can also be retrieved using the `docker images` command. The last image
you built should be at the top of the list.

Run

```sh
docker run -i -t --rm -p 8080:8000 $IMAGE_ID
```

where `$IMAGE_ID` is the image ID from before e.g. `55453fbf21c9`

The first few unique characters also work:

```sh
docker run -i -t --rm -p 8080:8000 5545
```

EOxServer is now accessible at [http://localhost:8080/](http://localhost:8080/).
And you can login to the `Admin Client` using:
- username: admin
- password: admin
