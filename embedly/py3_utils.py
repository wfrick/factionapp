import sys

# 2to3 doesn't handle the UserDict relocation
# put the import logic here for cleaner usage
try:
    from collections import UserDict as IterableUserDict
except ImportError:  # Python 2
    from UserDict import IterableUserDict


def python_2_unicode_compatible(klass):
    """
    A decorator that defines __unicode__ and __str__ methods under Python 2.
    Under Python 3 it does nothing.

    From django.utils.encoding.py in 1.4.2+, minus the dependency on Six.

    To support Python 2 and 3 with a single code base, define a __str__ method
    returning text and apply this decorator to the class.
    """
    if sys.version_info[0] == 2:
        if '__str__' not in klass.__dict__:
            raise ValueError("@python_2_unicode_compatible cannot be applied "
                             "to %s because it doesn't define __str__()." %
                             klass.__name__)
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda self: self.__unicode__().encode('utf-8')
    return klass
