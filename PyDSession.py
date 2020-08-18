from PyDAbsSession import PyDAbsSession, PyDException
import utils
import requests
import json

class PyDSession(PyDAbsSession):

    def __init__(self, config=None):
        PyDAbsSession.__init__(self, config)

    def search(self, code):
        url = self.url("/index.php", {"_action_": "backend"})
        rawdata = {
            "path": "/networks/" + self.config["network"] + "/libraries/" + self.config[
                "library"] + "/catalog/item/search/fulltext",
            "criteria": {"code": code, "networkId": self.config["network"], "sort": "code", "dir": "ASC",
                         "start": 0,
                         "limit": 20},
            "jsonParams": "criteria"
        }

        data = utils.encode_dict(rawdata)

        res = requests.post(url, headers={
            "content-type": 'application/x-www-form-urlencoded',
            'Cookie': 'eppk=' + self.cookies["eppk"]
        }, data=data)

        if res.status_code != 200:
            raise PyDException(PyDAbsSession.ERROR_STATUS, "Erreur, status : %d" % res.status_code)

        res= json.loads(res.text)
        id = res["res"]["executionId"]
        while True:
            res = self._progress("/catalog/item/search/%d/progress" % id)
            if res["res"]["execution"]["status"] == "COMPLETED":
                break

        res = self._progress("/catalog/item/search/%d/result/data" % id)
        return res["res"]["list"][0]

    def modify(self, js):
        data={}
        fields = [
            "id", "code", "depositaryLibraryId", "cote", "price", "discount",
            "discountedPrice", "creationDate", "publicAvailableDate", "note",
            "isNew", "isCreatedAsNew", "itemClassifications"
        ]
        for key in fields:
            data[key]=js[key]
            if not key in js:
                raise Exception("Le champ '%s' n'est pas dans le json du document" % key)

        fieldsId = ["localization", "subLocalization", "support", "targetAudience", "loanCategory",
                    "status", "owner", "collectionPeriodical", "targetOwner", "budgetLine", "provider"]
        for key in fieldsId:
            data[key+"Id"]= js[key]["id"] if js[key] else None
        data["computeIsNewPeriodAgain"]=None
        data["checkPeriodicalCoherency"]=True
        data["trap"]=js["bibRecord"]["trap"] if "trap" in js["bibRecord"] else None

        url=self.url("/index.php", {"_action_":"backend"})
        data=utils.encode_dict({
            "path": "/networks/" + self.config["network"] + "/libraries/" + self.config["library"] + "/catalog/bibRecords/items/job/addOrUpdate",
            "operation": "UPDATE",
            "libraryId": self.config["library"],
            "bibrecordId": js["bibRecord"]["id"],
            "addOrUpdateForm": json.dumps(data),
            "jsonParams": "addOrUpdateForm"
        })
        res = requests.post( url, headers={
            "content-type": 'application/x-www-form-urlencoded',
            'Cookie': 'eppk=' + self.cookies["eppk"]
        }, data=data)

        if res.status_code != 200:
            raise PyDException(PyDAbsSession.ERROR_STATUS, "Erreur, status : %d" % res.status_code)

        res= json.loads(res.text)
        id = res["res"]["executionId"]
        while True:
            res = self._progress("/catalog/bibRecords/items/job/addOrUpdate/%d/progress" % id)
            if res["res"]["execution"]["status"] == "COMPLETED":
                break

        res = self._progress("/catalog/bibRecords/items/job/addOrUpdate/%d/result" % id)
        return res


