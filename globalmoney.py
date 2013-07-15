#!/usr/bin/python
import cgi
import cgitb
import json
import dbmanager
import os
import datetime
import hashlib
import math

#cgitb.enable()
operator = 16

secret = 'secret'

dbmanager.init()
####errno : 1 - unknown user
####errno : 2 - error making payment
####errno : 3 - transaction exists
####errno : 4 - transaction not exists
####errno : 5 - bad chacksum

def check_hash(form):
    k = sorted(form.keys())
    raw = ''
    hs = ''
    for val in k:
    if(val != 'hash'):
        raw += str(form[val].value)
    else:
        hs = form[val].value
    m = hashlib.md5()
    raw += secret
    m.update(raw)
    return (m.hexdigest() == hs)

def process(form):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    aResult = {
        'datetime' : dt
    }
    if 'cmd' in form:
    cmd = form["cmd"].value
    if(cmd == 'check'):
        if('uid' in form):
        uid = int(form["uid"].value)
        result = dbmanager.check_user(uid)
        deposit = dbmanager.get_deposit2(uid)
        if deposit < 0:
            deposit = -deposit
        else:
            deposit = 0
        result.update({'deposit':math.ceil(deposit)})
        else:
        result = {'result':'error','errno':2,'status':'err_fields'}
        aResult.update(result)
    elif(cmd == 'pay'):
        if (('uid' in form) and ('summ' in form) and ('tid' in form)):
        uid = int(form["uid"].value)
        summ = float(form["summ"].value)
        tid = form["tid"].value
        ip=os.environ['REMOTE_ADDR']
        result = dbmanager.pay(uid,operator,summ,tid,ip)
        aResult.update(result)
        else:
        aResult.update({'result':'error','errno':2,'status':'err_fields'})
    elif(cmd == 'check_tid'):
        if('tid' in form):
        tid = form["tid"].value
        result = dbmanager.check_tid(tid)
        aResult.update(result)
        else:
        aResult.update({'result':'error','errno':2,'status':'err_fields'})
    else:
        aResult.update({'result':'error','errno':2,'status':'err_unknown_command'})
    else:
    aResult.update({'result':'error','errno':2,'status':'err_no_command'})
    raw = aResult['datetime']+aResult['result']+secret
    m = hashlib.md5()
    m.update(raw)
    aResult['hash'] = m.hexdigest()
    return aResult

print "Content-type: text/json\n\n";
form = cgi.FieldStorage()

if ('hash' in form) and (check_hash(form)):
    aResult = process(form)
else:
    aResult = {'result':'error','errno':'5','status':'bad_checksum'}

print json.dumps(aResult,indent=4)
