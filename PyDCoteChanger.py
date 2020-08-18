from PyDAbsSession import PyDAbsSession, PyDException
from PyDSession import PyDSession
import utils
import requests
import json

def tiret_to_space(cote):
    out=""
    for c in cote:
        if c=='-' or c==' ':
            if len(out)>00 and out[-1]!=' ':
                out+=' '
        else:
            out+=c
    return out

def space_to_tiret(cote):
    out=""
    for c in cote:
        if c=='-' or c==' ':
            if out[-1]!='-':
                out+='-'
        else:
            out+=c
    return out

class PyDCoteChanger(PyDSession):




    def __init__(self, config=None, fct=tiret_to_space):
        PyDSession.__init__(self, config)
        self.callback=fct
        self.log=[]

    def replace(self, code):
        print("\nCode: %s" %code)
        res=self.search(code)
        print("Cote: %s" % res["cote"])
        oldcote=res["cote"]
        old=json.dumps(res, indent=2).split("\n")
        res["cote"] = self.callback(res["cote"])
        res=self.modify(res)
        res=self.search(code)
        new=json.dumps(res, indent=2).split("\n")

        min = len(old) if len(old)<len(new) else len(new)
        n = len(new) - len(old)
        if n<0: n=-n

        i=0
        while i<min:
            if old[i] != new[i]:
                n+=1
                print("'%s' -> '%s' " % (old[i], new[i]))
            i+=1
        if n>1:
            self.log.append(("FAIL", oldcote, code, res["cote"]))
            print("Erreur dans la modification, plusierus champs ont été modifiés")
        else:
            self.log.append(("OK", oldcote, code, res["cote"]))
            print("Element modifié avec succès")
        return n

    @staticmethod
    def extract_cote(cote):
        out=""
        for c in cote:
            if c in "0123456789":
                out+=c
            else: return out
        return out

    def replace_from_file(self, filename):
        codes = []
        n=0
        with open(filename, "r") as f:
            codes=f.read().split("\n")
        for code in codes:
            code=PyDCoteChanger.extract_cote(code)
            if code:
                if self.replace(code)>1:
                    return n
                else: n+=1
        return n







