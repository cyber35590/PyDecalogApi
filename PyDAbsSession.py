import requests
import json
import utils

class PyDException(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self)
        self.code=code
        self.msg=msg

class PyDAbsSession:
    STATE_UNCONNECTED="STATE_UNCONNECTED"
    STATE_CONNECTED = "STATE_CONNECTED"
    STATE_DISCONNECTED = "STATE_DISCONNECTED"
    SUCCESS = "SUCCESS"
    ERROR_HANDSHAKE = "ERROR_HANDSHAKE"
    ERROR_DATA = "ERROR_DATA"
    ERROR_STATUS = "ERROR_STATUS"
    ERROR_DISCONNECTED = "ERROR_DISCONNECTED"
    ERROR_NON_UNIQUE_CODE = "ERROR_NON_UNIQUE_CODE"

    @staticmethod
    def extract_decalog_data(res):
        out={}
        lines=res.text.split("\n")
        for line in lines:
            if "<form" in line:
                tmp=line[line.find("action=")+8:]
                tmp=tmp[:tmp.find('"')]
                out["url"]=tmp
            if 'name="lt"' in line:
                tmp=line[line.find('value="')+7:]
                tmp=tmp[:tmp.find('"')]
                out["lt"]=tmp
        return out


    @staticmethod
    def encode_cookies(cookies):
        return  "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])

    def __init__(self, config=None):
        """
        :param config: {
              "url": "https://xxxxx.xxx",
              "user": "xxx@xxx.xxx",
              "password": "xxx",
              "network": "xxxxx",
              "library": "xxxxx"
            }
        """
        if not config:
            with open("user.json") as f:
                config=json.loads(f.read())
        self.config=config
        self.cookies={}
        self.state=PyDAbsSession.STATE_UNCONNECTED
        self.auth_url=None

    def url(self, path="/", attr=None):
        url=self.config["url"]+path
        if attr:
            url+="?"
            i=0
            for key in attr:
                if i>0:
                    url+="&"
                val=attr[key]
                url+=utils.urlencode(key)+"="+utils.urlencode(val)
                i+=1
        return url

    def _connect_init(self):
        url = self.url("/cas/login", { "service" : self.config["url"]+"/index.php?_action_=auth" } )
        res=requests.get(url, headers={
          "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0",
          "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          'content-type': 'application/x-www-form-urlencoded',
          "Connection": "close",
          'Upgrade-Insecure-Requests': '1',
          'Referer': 'https://sigb02.decalog.net/cas/login?service=https%3A%2F%2Fsigb02.decalog.net%2Findex.php%3F_action_%3Dauth',
          'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3'
        }, allow_redirects = False)
        if res.status_code==200:
            cookies=dict(res.cookies)
            if not "JSESSIONID" in cookies:
                raise PyDException(PyDAbsSession.ERROR_HANDSHAKE, "Impossible d'obtenir le JSESSIONID")
            self.cookies["JSESSIONID"]=cookies["JSESSIONID"]

            return res
        else:
            raise PyDException(PyDAbsSession.ERROR_STATUS, "Status: %d " % res.status_code)



    def _connect_ticket(self, url, lt):
        data=utils.encode_dict({
            "username" : self.config["user"],
            "password" : self.config["password"],
            "lt" : lt,
            "submit": "SE+CONNECTER",
            "_eventId": "submit"
        })
        nurl = self.config["url"]+url

        res=requests.post(nurl, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'content-type': 'application/x-www-form-urlencoded',
            "Connection": "close",
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            "Cookie" : PyDAbsSession.encode_cookies({ "JSESSIONID" : self.cookies["JSESSIONID"]})
            }, data=data, allow_redirects=False)

        if res.status_code==302:
            location=""
            if (not "location" in res.headers) and (not "Location" in res.headers):
                raise PyDException(PyDAbsSession.ERROR_DATA, res)
            if "location" in res.headers : location=res.headers["location"]
            elif "Location" in res.headers : location=res.headers["Location"]
            self.auth_url=location
            return res
        else:
            raise PyDException(PyDAbsSession.ERROR_STATUS, "Status: %d (doit normalement être 302)" % res.status_code)

    def _connect_auth(self):
        res=requests.get(self.auth_url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'content-type': 'application/x-www-form-urlencoded',
            "Connection": "close",
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            "Cookie": PyDAbsSession.encode_cookies({"JSESSIONID": self.cookies["JSESSIONID"]})
        }, allow_redirects=False)

        if res.status_code==302:
            cookies=dict(res.cookies)
            if not "eppk" in cookies:
                raise PyDException(PyDAbsSession.ERROR_DATA, "Le cookie eppk n'est pas présent dans la réponse")
            self.cookies["eppk"]=cookies["eppk"]
            return res
        else:
            raise PyDException(PyDAbsSession.ERROR_STATUS, "Status: %d (doit normalement être 302)" % res.status_code)

    def _connect_valid(self):
        res=requests.get(self.url("/index.php", {"_action_" : "change_workspace"}), headers={
          "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0",
          "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          'content-type': 'application/x-www-form-urlencoded',
          "Connection": "close",
          'Upgrade-Insecure-Requests': '1',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'DNT' : '1',
          'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3' ,
          "Cookie": PyDAbsSession.encode_cookies({"eppk": self.cookies["eppk"]})
        })
        return res

    def _progress(self, url):
        url = self.url("/index.php", {
            "_action_": "backend",
            "path": "/networks/" + str(self.config["network"]) + "/libraries/" + str(
                self.config["library"]) + url
        })

        res = requests.get(url, headers={
            "content-type": 'application/x-www-form-urlencoded',
            'Cookie': 'eppk=' + self.cookies["eppk"]
        })

        if res.status_code != 200:
            raise PyDException(PyDAbsSession.ERROR_STATUS, "Erreur, status : %d" % res.status_code)

        return json.loads(res.text)

    def connect(self):
        res= self._connect_init()
        obj = PyDAbsSession.extract_decalog_data(res)
        res=self._connect_ticket(obj["url"], obj["lt"])
        res=self._connect_auth()
        res=self._connect_valid()
        if res.status_code==200:
            self.state=PyDAbsSession.STATE_CONNECTED






