# Python 3.10+ Modernization Plan

## Type Hinting Improvements

### Union Types
Replace `Union[X, Y]` with `X | Y` syntax:
- `Union[str, Dict[str, Any]]` → `str | Dict[str, Any]`
- `Union[Person, Application, Group, Organization, Service]` → `Person | Application | Group | Organization | Service`
- `Union[str, ObjectType]` → `str | ObjectType`
- `Optional[X]` → `X | None`

### Better Type Annotations
- Add proper type hints to all functions and methods
- Use `typing.Protocol` for structural subtyping where appropriate
- Use `typing.TypedDict` for dictionary structures
- Use `typing.Literal` for literal values

## Structural Pattern Matching

### Activity Type Parsing
Replace complex if/elif chains with match statements:
```python
# Current approach
def parse_activity(payload: ObjectType, expected: Optional[ActivityType] = None) -> "BaseActivity":
    if "type" not in payload:
        raise BadActivityError(f"the payload has no type: {payload!r}")

    t = ActivityType(_to_list(payload["type"])[0])

    if expected and t != expected:
        raise UnexpectedActivityTypeError(
            f'expected a {expected.name} activity, got a {payload["type"]}: {payload}'
        )

    if t not in _ACTIVITY_CLS:
        raise BadActivityError(
            f'unsupported activity type {payload["type"]}: {payload}'
        )

    activity = _ACTIVITY_CLS[t](**payload)
    return activity

# Modern approach with pattern matching
def parse_activity(payload: ObjectType, expected: ActivityType | None = None) -> "BaseActivity":
    match payload:
        case {"type": activity_type}:
            t = ActivityType(_to_list(activity_type)[0])
        case _:
            raise BadActivityError(f"the payload has no type: {payload!r}")
    
    match expected, t:
        case expected_type, activity_type if expected_type and activity_type != expected_type:
            raise UnexpectedActivityTypeError(
                f'expected a {expected_type.name} activity, got a {payload["type"]}: {payload}'
            )
        case _:
            pass
    
    match t:
        case activity_type if activity_type in _ACTIVITY_CLS:
            return _ACTIVITY_CLS[activity_type](**payload)
        case _:
            raise BadActivityError(
                f'unsupported activity type {payload["type"]}: {payload}'
            )
```

### Object Type Handling
Use pattern matching for object type validation:
```python
# Current approach
if isinstance(obj, str):
    # The object is a just a reference the its ID/IRI
    # FIXME(tsileo): fetch the ref
    self._data["object"] = obj
elif isinstance(obj, dict):
    if not self.ALLOWED_OBJECT_TYPES:
        raise UnexpectedActivityTypeError("unexpected object")
    if "type" not in obj or (
        self.ACTIVITY_TYPE != ActivityType.CREATE and "id" not in obj
    ):
        raise BadActivityError("invalid object, missing type")
    if not _has_type(  # type: ignore  # XXX too complicated
        obj["type"], self.ALLOWED_OBJECT_TYPES
    ):
        raise UnexpectedActivityTypeError(
            f'unexpected object type {obj["type"]} (allowed={self.ALLOWED_OBJECT_TYPES!r})'
        )
    self._data["object"] = obj
else:
    raise BadActivityError(
        f"invalid object type ({type(obj).__qualname__}): {obj!r}"
    )

# Modern approach with pattern matching
match obj:
    case str():
        # The object is a just a reference the its ID/IRI
        # FIXME(tsileo): fetch the ref
        self._data["object"] = obj
    case {"type": obj_type, **rest} if self.ALLOWED_OBJECT_TYPES:
        if self.ACTIVITY_TYPE != ActivityType.CREATE and "id" not in obj:
            raise BadActivityError("invalid object, missing type")
        if not _has_type(obj_type, self.ALLOWED_OBJECT_TYPES):
            raise UnexpectedActivityTypeError(
                f'unexpected object type {obj_type} (allowed={self.ALLOWED_OBJECT_TYPES!r})'
            )
        self._data["object"] = obj
    case {"type": _, **rest} if not self.ALLOWED_OBJECT_TYPES:
        raise UnexpectedActivityTypeError("unexpected object")
    case dict():
        raise BadActivityError("invalid object, missing type")
    case _:
        raise BadActivityError(
            f"invalid object type ({type(obj).__qualname__}): {obj!r}"
        )
```

## Parenthesized Context Managers
Use parenthesized context managers for better readability:
```python
# Current approach
with open(file1) as f1, open(file2) as f2, open(file3) as f3:
    # process files

# Modern approach
with (
    open(file1) as f1,
    open(file2) as f2,
    open(file3) as f3,
):
    # process files
```

## Better Error Messages with Precise Location Information
Use the enhanced error locations in traceback (Python 3.11+ feature that builds on 3.10 improvements).

## Performance Improvements
- Use `functools.cache` instead of `functools.lru_cache(maxsize=None)`
- Leverage faster dictionary implementation
- Use more efficient string methods where applicable

## Modern String Formatting
Replace `.format()` and `%` formatting with f-strings:
```python
# Current approach
"expected a {expected.name} activity, got a {payload["type"]}: {payload}".format(expected=expected, payload=payload)

# Modern approach
f'expected a {expected.name} activity, got a {payload["type"]}: {payload}'
```

## Using the Walrus Operator
Use the walrus operator (:=) for assignments within expressions:
```python
# Current approach
actor = kwargs.get("actor")
if actor:
    kwargs.pop("actor")
    actor = self._validate_actor(actor)
    self._data["actor"] = actor

# Modern approach
if actor := kwargs.get("actor"):
    kwargs.pop("actor")
    actor = self._validate_actor(actor)
    self._data["actor"] = actor
```

## Improved Decorators
Use the new decorator syntax for better type checking and readability.

## Modern Exception Handling
Use exception groups and notes for better error reporting (Python 3.11 features that build on 3.10).

## Standard Library Improvements
- Use `importlib.metadata` instead of `importlib_metadata` (already partially implemented)
- Use `zoneinfo` instead of `pytz` for timezone handling
- Use `graphlib` for dependency resolution where applicable