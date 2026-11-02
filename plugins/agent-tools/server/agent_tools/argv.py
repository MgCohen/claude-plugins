"""Turn an args template plus validated arguments into an argv list.

One placeholder at most in each template element:
  {x}          the value; the element is an error if x has no value
  {x?}         the element is dropped if x has no value
  {x*}         the element repeats for each item of list x (dropped if empty)
  {x|--flag}   the element becomes --flag if boolean x is true, else it is dropped
Text around the placeholder stays: "--doc={doc?}" -> "--doc=spec".
"""
import re

PH = re.compile(r"\{([a-z][a-z0-9_]*)(\?|\*|\|[^}]*)?\}")


def placeholder_modes(template):
    """{name: mode}; mode is "", "?", "*" or "|"."""
    modes = {}
    for el in template:
        found = PH.findall(el)
        if len(found) > 1:
            raise ValueError(f"one placeholder at most in each element: {el!r}")
        for n, mod in found:
            m = mod[:1]
            if modes.get(n, m) != m:
                raise ValueError(f"placeholder {n!r} is used with different modifiers")
            modes[n] = m
    return modes


def placeholders(template):
    return set(placeholder_modes(template))


def build(command, template, args):
    out = list(command)
    for el in template:
        m = PH.search(el)
        if not m:
            out.append(el)
            continue
        name, mod = m.group(1), m.group(2) or ""
        pre, post = el[:m.start()], el[m.end():]
        v = args.get(name)
        if mod.startswith("|"):
            if v is True:
                out.append(pre + mod[1:] + post)
            continue
        if mod == "*":
            for item in (v or []):
                s = _text(item)
                if not pre and s.startswith("-"):
                    raise ValueError(f"items of {name!r} must not start with '-'")
                out.append(pre + s + post)
            continue
        if v is None:
            if mod == "?":
                continue
            raise ValueError(f"{name!r} has no value")
        s = _text(v)
        if not pre and s.startswith("-"):
            raise ValueError(f"{name!r} must not start with '-'")  # it would read as an option
        out.append(pre + s + post)
    return out


def _text(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)
