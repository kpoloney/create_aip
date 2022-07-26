import requests
import os

def get_node_json(repo_url, nid):
    n_url = repo_url + "/node/" + nid + "?_format=json"
    r = requests.get(n_url)
    if r.status_code==200:
        nodejson = r.json()
        return nodejson
    else:
        return "invalid url"

def get_members(repo_url, nid, user, pw):
    mem_url = repo_url + "/node/" + nid + "/members?_format=json"
    r = requests.get(mem_url, auth=(user,pw))
    if r.status_code == 200:
        membersjson = r.json()
        return membersjson
    else:
        return "invalid url"

def get_field_model(url):
    r = requests.get(url)
    if r.status_code == 200:
        taxonomy = r.json()
        model = taxonomy['field_external_uri'][0]['uri']
        return model
    else:
        return "invalid url"
