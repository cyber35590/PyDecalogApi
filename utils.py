from urllib import parse
import json

def dictassign(dest, *sources):
    for d in sources:
        for key in d:
            dest[key]=d[key]
    return dest

def dictcopy(*sources):
    return dictassign({}, *sources)


def urlencode(x):
    return parse.quote_plus(x)

def urldecode(x):
    return parse.quote_plus(x)

def encode_dict(opt):
    out=""
    i=0
    for key in opt:
        if i>0:
            out+="&"
        if isinstance(opt[key], dict):
            val = urlencode(json.dumps(opt[key]))
        else:
            val=urlencode(opt[key])
        out+="%s=%s" % (key, val)
        i+=1
    return out