import requests
import PyDCoteChanger



session = PyDCoteChanger.PyDCoteChanger(fct=PyDCoteChanger.space_to_tiret)
session.connect()
print(session.replace_from_file("test"))