# Contributing

## EOxServer code style guide

This section tries to establish a set of rules to help harmonizing the source 
code written by many contributors. The goal is to improve compatibility and 
maintainability.

Above all rules, adhere the rules defined in the [Python PEP 8](https://www.python.org/dev/peps/pep-0008/). Please try to adhere the 
mentioned code styles. You can check if you compliant to the style guide with
the `flake8` command line utilities.

Then:
```
>>> import this
The Zen of Python, by Tim Peters

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
```

### Package layout and namespacing

Use Python package structures to enable hierarchical namespaces. Do not encode
the namespace in function or class names.

E.g: don't do this:
```python
# somemodule.py

def myNS_FunctionA():
    pass

class myNS_ClassB():
    pass
```
Instead, do this:
```python
# somemodule/myNS.py

def functionA():
    pass

class ClassB():
    pass
```

A developer using these functions can choose to use the namespace explicitly:
```
from somepackage import myNS

myNS.functionA()
c = myNS.ClassB()
```

# Import rules

As defined in Python PEP 8, place all imports in the top of the file. This makes
it easier to trace dependencies and allows to see and resolve importing issues.

Try to use the following importing order:

1. Standard library imports or libraries that can be seen as industry standard (like numpy).
2. Third party libraries (or libraries that are not directly associated with the current project). E.g: GDAL, Django, etc.
3. Imports that are directly associated with the current project. In case of EOxServer, everything that is under the :mod:`eoxserver` package root.

Use single empty lines to separate these import groups.

## Coding guidelines

### Minimizing pitfalls

Don't use mutable types as default arguments

As default arguments are evaluated at the time the module is imported and not 
when the function/method is called, default arguments are a sort of global 
variable and calling the function can have unintended side effects. Consider the
following example:
```python
    def add_one(arg=[]):
        arg.append(1)
        print arg
```
When called with no arguments, the function will print different results every 
time it is invoked. Also, since the list will never be released, this is also a
memory leak, as the list grows with the time.


Don't put code in the `__init__.py` of a package

When importing a package or a module from a package, the packages 
`__init__.py` will first be imported. If there is production code included 
(which will likely be accompanied by imports) this can lead to unintended 
circular imports. Try to put all production code in modules instead, and use the
`__init__.py` only for really necessary stuff.


Use abbreviations sparingly

Try not to use abbreviations, unless the meaning is commonly known. Examples 
are HTTP, URL, WCS, BBox or the like.

Don't use leading double underscores to specify 'private' fields or methods or 
module functions, unless *really* necessary (which it isn't, usually). Using 
double underscores makes it unnecessarily hard to debug methods/fields and is 
still not really private, as compared to other languages like C++ or Java. Use 
single leading underscores instead. The meaning is clear to any programmer and 
it does not impose any unnecessary comlications during debugging.


## Improving tests

### General rules

Implementing new features shall *always* incorporate writing new tests! Try to
find corner/special cases and also try to find cases that shall provoke 
exceptions.

Where to add the tests?

Try to let tests *fail* by calling the correct assertion or the 
`fail` functions. Don't use exceptions (apart from `AssertionError`), 
because when running the tests, this will be visible as "Error" and not a simple 
failure. Test errors should indicate that something completely unexpected 
happened that broke the testing code.

For more information on development check out [the docs](https://docs.eoxserver.org/en/stable/developers/index.html)
