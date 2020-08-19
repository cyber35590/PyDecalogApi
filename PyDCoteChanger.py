from PyDAbsSession import PyDAbsSession, PyDException
from PyDSession import PyDSession
import utils
import requests
import time
import json
from  PyDb import LogEntry, PyDb

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
        self.logdb=PyDb()
        self.log=[]

    def replace(self, code):
        start=time.time()
        le = LogEntry(code)
        print("Code: %s" %code)
        res=self.search(code)
        with open("sources/%s.json" % code, "w") as f:
            f.write(json.dumps(res, indent=2))
        print("Cote: %s" % res["cote"])
        le.set_before(res)
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

        with open("sources/%s.new.json" % code, "w") as f:
            f.write(json.dumps(res, indent=2))
        if n>1:
            self.log.append(("FAIL", oldcote, code, res["cote"]))
            print("Erreur dans la modification, plusierus champs ont été modifiés\n")
            le.set_after(res)
            self.logdb.logobject(le)
        else:
            self.log.append(("OK", oldcote, code, res["cote"]))
            le.set_after(res)
            self.logdb.logobject(le)
            print("Nouvelle cote : '%s'"%res["cote"])
            print("Element modifié avec succès en %.3f s\n" % (time.time()-start))
        return n

    @staticmethod
    def extract_cote(cote):
        out=""
        for c in cote:
            if c in "0123456789":
                out+=c
            else: return out
        return out

    def replace_from_file(self, filename, logname="log.csv"):
        with open(logname, "w") as logfile:
            codes = []
            n=0
            with open(filename, "r") as f:
                codes=f.read().split("\n")
            lines=len(codes)
            current_line=1
            for code in codes:
                print("Élément %d/%d (%.2f %%)" % (current_line, lines, (current_line*100/lines)))
                code=PyDCoteChanger.extract_cote(code)
                if code:
                    if self.replace(code)>1:
                        self.write_last_log(logfile)
                        break

                    else:
                        self.write_last_log(logfile)
                        n+=1
                        current_line += 1

        return n

    def write_last_log(self, fd):
        row=self.log[-1]
        out=""
        for c in row:
            out += '"%s";' % c
        fd.write("%s\n" % out)
        fd.flush()

    def log_to_str(self):
        out=""
        for row in self.log:
            for c in row:
                out+='"%s";' % c
            out+="\n"
        return out

    def write_log(self, file="log.csv"):
        with open(file, "w") as f:
            f.write(self.log_to_str())


