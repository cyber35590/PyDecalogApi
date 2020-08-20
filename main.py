import requests
import PyDCoteChanger
import PyDb


session = PyDCoteChanger.PyDCoteChanger()
session.connect()
print(session.replace_from_file("exemplaires.txt"))
#session.replace("0013121888")