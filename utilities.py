
from __future__ import division, print_function, unicode_literals

import re

try:
    from htmlentitydefs import name2codepoint
except ImportError:
    # Must be Python 3.x
    from html.entities import name2codepoint
    unichr = chr


def unescaper(match):
    """Custom un-escape function.

    """
    name2codepoint_work = name2codepoint.copy()
    name2codepoint_work['apos']=ord("'")

    code = match.group(1)
    if code:
        return unichr(int(code, 10))
    else:
        code = match.group(2)
        if code:
            return unichr(int(code, 16))
        else:
            code = match.group(3)
            if code in name2codepoint_work:
                return unichr(name2codepoint_work[code])

    return match.group(0)


def decode(s, encoding='utf-8'):
    """Decode string entity.

    """
    EntityPattern = re.compile(u'&(?:#(\d+)|(?:#x([\da-fA-F]+))|([a-zA-Z]+));')
    result = EntityPattern.sub(unescaper, s.decode(encoding))

    return result


def extract_url(text):
    result = re.search("(?P<url>https?://[^\s]+)", text)
    if result:
        url = result.group("url")
    else:
        url = None

    return url


#####################################################

if __name__ == '__main__':
    # quick example.

    t1 = 'franchise&#039;s'
    # t1 = 'Str&#246;m'
    t2 = decode(t1)

    print(t1)
    print(t2)
