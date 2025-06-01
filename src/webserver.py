import os
import requests
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from pysnmp.hlapi.v3arch.asyncio import *
import uvicorn
import feedparser
import hashlib
import json
import threading
import time

app = FastAPI()
load_dotenv()

DSM_HOST = os.getenv('DSM_HOST')
USERNAME = os.getenv('DSM_USERNAME')
PASSWORD = os.getenv('DSM_PASSWORD')

SNMP_HOST = os.getenv('SNMP_HOST')
SNMP_USERNAME = os.getenv('SNMP_USERNAME')
SNMP_PASSWORD = os.getenv('SNMP_PASSWORD')

DATABASE_DIRECTORY = os.getenv('STORAGE_DIR', '/app/storage') 
FEED_FILE = os.getenv('FEED_FILE', '/app/config/feed.json')
LISTEN_PORT = os.getenv('LISTEN_PORT', 8000)

def get_system_temp(sid):
    url = f'{DSM_HOST}/webapi/entry.cgi'
    payload = {
        'api': 'SYNO.Core.System',
        'method': 'info',
        'version': '1',
        "_sid": sid
    }
    r = requests.post(url, data=payload, verify=False)
    r.raise_for_status()
    body = r.json()
    return body.get('data', {}).get('sys_temp', 0)

async def get_disk_temps(ipaddress, username, passwd):
    temps = {}
    oids = [
        ObjectType(ObjectIdentity('1.3.6.1.4.1.6574.2.1.1.2')),
        ObjectType(ObjectIdentity('1.3.6.1.4.1.6574.2.1.1.3')),
        ObjectType(ObjectIdentity('1.3.6.1.4.1.6574.2.1.1.6'))
    ]

    errorIndication, errorStatus, errorIndex, varBinds = await bulk_cmd(
        SnmpEngine(),
        UsmUserData(username, passwd, authProtocol=usmHMACSHAAuthProtocol),
        await UdpTransportTarget.create((ipaddress, 161)),
        ContextData(),
        0, 10,
        *oids
    )

    if errorIndication or errorStatus:
        print("SNMP hiba:", errorIndication or errorStatus.prettyPrint())
        return temps

    disk_data = {}
    for varBind in varBinds:
        oid, value = varBind
        oid_str = str(oid)

        index = oid_str.split('.')[-1]
        if index not in disk_data:
            disk_data[index] = {}

        if oid_str.startswith('1.3.6.1.4.1.6574.2.1.1.2'):
            disk_data[index]['name'] = str(value)
        elif oid_str.startswith('1.3.6.1.4.1.6574.2.1.1.3'):
            disk_data[index]['model'] = str(value)
        elif oid_str.startswith('1.3.6.1.4.1.6574.2.1.1.6'):
            disk_data[index]['temperature'] = int(value)

    for index, info in disk_data.items():
        temps[f'disk{index}'] = info.get('temperature', 'Unknown')

    return temps

def get_sid():
    url = f"{DSM_HOST}/webapi/auth.cgi"
    params = {
        "api": "SYNO.API.Auth",
        "version": "6",
        "method": "login",
        "account": USERNAME,
        "passwd": PASSWORD,
        "session": "DownloadStation",
        "format": "sid"
    }
    r = requests.get(url, params=params, verify=False)
    r.raise_for_status()
    return r.json()["data"]["sid"]
    
@app.get("/temps")
async def temps_api():
    temps = {}
    temps = await get_disk_temps(SNMP_HOST, SNMP_USERNAME, SNMP_PASSWORD)
    temps['cpu'] = get_system_temp(get_sid())
    #print(temps)
    return temps



if __name__ == "__main__":
    uvicorn.run("webserver:app", host="0.0.0.0", port=LISTEN_PORT, reload=True)