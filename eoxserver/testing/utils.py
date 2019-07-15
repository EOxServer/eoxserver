def tag(*tags):
    """Decorator to add tags to a test class or method."""
    def decorator(obj):
        if len(getattr(obj, '__bases__', [])) > 1:
            setattr(obj, 'tags', set(tags).union(*[
                set(base.tags)
                for base in obj.__bases__
                if hasattr(base, 'tags')
            ]))
        elif hasattr(obj, 'tags'):
            obj.tags = obj.tags.union(tags)
        else:
            setattr(obj, 'tags', set(tags))
        return obj
    return decorator
