import sqlite3
import base64
import json
import difflib

CREATE_SCHEM="""
create table operation (
    id int PRIMARY_KEY,
    code text,
    before text,
    after text,
    diff text
)
"""


def encode(x): return base64.b64encode(x.encode()).decode()
def decode(x): return base64.b64decode(x.encode()).decode("utf8")

def diff(a, b):
    diff = difflib.unified_diff(a.split("\n"), b.split("\n"))
    out=""
    for line in diff:
        if line[0] in "+-@":
            out+=line+"\n"
    return out

class LogEntry:
    def __init__(self, code):
        self.id=-1
        self.code=code
        self.before=""
        self.after=""
        self.diff=""

    def set_before(self, obj):
        self.before=json.dumps(obj, indent=2)

    def set_after(self, obj):
        self.after=json.dumps(obj, indent=2)
        self.diff=diff(self.before, self.after)


class PyDb:
    def __init__(self, filename="log.db"):
        self.db = sqlite3.connect(filename)
        if len(self.tables())==0:
            self.execute(CREATE_SCHEM)
            self.commit()
        tmp=self.execute("select max(id) from operation")
        self.current_id=tmp[0][0]+1 if len(tmp) and tmp[0][0]!=None else 0

    def log(self, code, before, after):
        self.current_id += 1
        self.execute("insert into operation (id, code, before, after, diff) values (%d, '%s', '%s', '%s', '%s')" % (self.current_id, code, encode(before), encode(after), encode(diff(before, after))))
        self.commit()

    def find_log_code(self, code):
        x=self.execute("select * from operation where code='%s' " % code)
        out = {}
        for row in x:
            x=LogEntry(row[1])
            x.id=row[0]
            x.before=decode(row[2])
            x.after=decode(row[3])
            x.diff=decode(row[4])
            out[x.code]=x
        return out


    def find_log_id(self, id):
        x=self.execute("select * from operation where id=%d " % id)
        out = {}
        for row in x:
            x=LogEntry(row[1])
            x.id=row[0]
            x.before=decode(row[2])
            x.after=decode(row[3])
            x.diff=decode(row[4])
            out[x.code]=x
        return out

    def logobject(self, l : LogEntry):
        self.current_id += 1
        if l.id<0:
            l.id=self.current_id

        self.execute("insert into operation (id, code, before, after, diff) values (%d, '%s', '%s', '%s', '%s')" %(l.id, l.code, encode(l.before), encode(l.after), encode(l.diff)))
        self.commit()

    def tables(self):
        return self.execute("SELECT name FROM sqlite_master WHERE type='table';")

    def execute(self, query):
        print(query)
        return self.db.execute(query).fetchall()

    def commit(self): self.db.commit()


log = PyDb()