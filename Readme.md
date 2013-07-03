# Documentation HowTo

## Generate Sphinx documentation

### UNIX

```sh
cd <path_to_docs_directory>/sphinx
export PYTHONPATH="<PATH-TO-EOxServer-CODE>"
export DJANGO_SETTINGS_MODULE="autotest.settings" # Use a valid EOxServer settings file here. Note that the configured database needs to be synced.
make html
```

The documentation is generated in *_build/html*.

```sh
# For pdf output run:
make latex
cd _build/latex/
make all-pdf
```

The pdf documentation is generated as *EOxServer.pdf*.

### Windows

```sh
cd <path_to_docs_directory>/sphinx
set PYTHONPATH="<PATH-TO-EOxServer-CODE>"
set DJANGO_SETTINGS_MODULE="autotest.settings" # Use a valid EOxServer settings file here. Note that the configured database needs to be synced.
sphinx-build.exe -b html -d _build\doctrees -D latex_paper_size=a4 . _build/html  #Note that the "sphinx-build.exe" has to be set in your path
````

The documentation is generated in *_build/html*.

## Generate epydoc documentation

```sh
cd <path_to_eoxserver_directory>
export DJANGO_SETTINGS_MODULE="autotest.settings"
epydoc --name=EOxServer --output=../docs/epydoc/ --html --docformat=javadoc --graph=all .
```

## Update model graphs

```sh
cd <path_to_autotest_directory>
python manage.py graph_models --output=../docs/sphinx/en/developers/images/model_core.png core
python manage.py graph_models --output=../docs/sphinx/en/developers/images/model_services.png services
python manage.py graph_models --output=../docs/sphinx/en/developers/images/model_coverages.png coverages
python manage.py graph_models --output=../docs/sphinx/en/developers/images/model_backends.png backends

python manage.py graph_models coverages --output=./tmp.dot
# Edit tmp.dot and remove top lines up to "digraph name {".
dot -Tsvg ./tmp.dot -o./tmp.svg
# Edit tmp.svg e.g. with Inkscape
```
