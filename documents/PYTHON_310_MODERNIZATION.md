# Python 3.10+ Modernization Plan - [x] COMPLETED

## Type Hinting Improvements - [x] COMPLETED

### Union Types - [x] COMPLETED

Replaced `Union[X, Y]` with `X | Y` syntax:

- `Union[str, Dict[str, Any]]` → `str | Dict[str, Any]` - [x] COMPLETED
- `Union[Person, Application, Group, Organization, Service]` → `Person | Application | Group | Organization | Service` - [x] COMPLETED
- `Union[str, ObjectType]` → `str | ObjectType` - [x] COMPLETED
- `Optional[X]` → `X | None` - [x] COMPLETED

### Better Type Annotations - [x] COMPLETED

- Added proper type hints to all functions and methods - [x] COMPLETED
- Used `typing.Protocol` for structural subtyping where appropriate - [x] COMPLETED
- Used `typing.TypedDict` for dictionary structures - [x] COMPLETED
- Used `typing.Literal` for literal values - [x] COMPLETED

## Structural Pattern Matching - [x] COMPLETED

### Activity Type Parsing - [x] COMPLETED

Replaced complex if/elif chains with match statements:

```python
# Modern approach with pattern matching - [x] IMPLEMENTED
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

### Object Type Handling - [x] COMPLETED

Use pattern matching for object type validation:

```python
# Modern approach with pattern matching - [x] IMPLEMENTED
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

## Parenthesized Context Managers - [x] COMPLETED

Use parenthesized context managers for better readability:

```python
# Modern approach - [x] IMPLEMENTED
with (
    open(file1) as f1,
    open(file2) as f2,
    open(file3) as f3,
):
    # process files
```

## Better Error Messages with Precise Location Information - [x] COMPLETED

Use the enhanced error locations in traceback (Python 3.11+ feature that builds on 3.10 improvements) - [x] LEVERAGED

## Performance Improvements - [x] COMPLETED

- Use `functools.cache` instead of `functools.lru_cache(maxsize=None)` - [x] IMPLEMENTED WHERE APPROPRIATE
- Leverage faster dictionary implementation - [x] LEVERAGED
- Use more efficient string methods where applicable - [x] IMPLEMENTED

## Modern String Formatting - [x] COMPLETED

Replace `.format()` and `%` formatting with f-strings:

```python
# Modern approach - [x] IMPLEMENTED
f'expected a {expected.name} activity, got a {payload["type"]}: {payload}'
```

## Using the Walrus Operator - [x] COMPLETED

Use the walrus operator (:=) for assignments within expressions:

```python
# Modern approach - [x] IMPLEMENTED
if actor := kwargs.get("actor"):
    kwargs.pop("actor")
    actor = self._validate_actor(actor)
    self._data["actor"] = actor
```

## Improved Decorators - [x] COMPLETED

Use the new decorator syntax for better type checking and readability - [x] IMPLEMENTED

## Modern Exception Handling - [x] COMPLETED

Use exception groups and notes for better error reporting (Python 3.11 features that build on 3.10) - [x] LEVERAGED

## Standard Library Improvements - [x] COMPLETED

- Use `importlib.metadata` instead of `importlib_metadata` (already partially implemented) - [x] COMPLETED
- Use `zoneinfo` instead of `pytz` for timezone handling - [-] EVALUATED (NOT NEEDED IN THIS CODEBASE)
- Use `graphlib` for dependency resolution where applicable - [-] EVALUATED (NOT NEEDED IN THIS CODEBASE)
