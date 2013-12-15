import re
try:
    from htmlentitydefs import name2codepoint
except ImportError:
    # Must be Python 3.x
    from html.entities import name2codepoint
    unichr = chr

name2codepoint = name2codepoint.copy()
name2codepoint['apos']=ord("'")

EntityPattern = re.compile('&(?:#(\d+)|(?:#x([\da-fA-F]+))|([a-zA-Z]+));')


def unescape(match):
    """Custom un-escape function.
    """
    code = match.group(1)
    if code:
        return unichr(int(code, 10))
    else:
        code = match.group(2)
        if code:
            return unichr(int(code, 16))
        else:
            code = match.group(3)
            if code in name2codepoint:
                return unichr(name2codepoint[code])
    return match.group(0)


def decode(s, encoding='utf-8'):
    """Decode string entity.
    """
    return EntityPattern.sub(unescape, s.decode(encoding))

#####################################################

if __name__ == '__main__':
    # quick example.

    t1 = 'franchise&#039;s'
    # t1 = 'Str&#246;m'
    t2 = decode(t1)

    print(t1)
    print(t2)

