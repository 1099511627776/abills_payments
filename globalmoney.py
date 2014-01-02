#!/usr/bin/python
import cgi
import json
import dbmanager
import os
import datetime
import hashlib
import math

OPERATOR = 16
SECRET = 'secret'

dbmanager.init()
####errno : 1 - unknown user
####errno : 2 - error making payment
####errno : 3 - transaction exists
####errno : 4 - transaction not exists
####errno : 5 - bad chacksum

def check_hash(form):
    """ Checking hash of the packet"""
    k = sorted(form.keys())
    raw = ''
    hs = ''
    for val in k:
        if val != 'hash':
            raw += str(form[val].value)
        else:
            hs = form[val].value
    m = hashlib.md5()
    raw += SECRET
    m.update(raw)
    return m.hexdigest() == hs

def process(frm):
    """ Main program process"""
    aResult = {
        'datetime' : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if 'cmd' in frm:
        cmd = frm["cmd"].value
        if cmd == 'check':
            if 'uid' in frm:
                uid = int(frm["uid"].value)
                result = dbmanager.check_user(uid)
                deposit = dbmanager.get_deposit2(uid)
                if deposit < 0:
                    deposit = -deposit
                else:
                    deposit = 0
                result.update({'deposit':math.ceil(deposit)})
            else:
                result = {'result':'error', 'errno':2, 'status':'err_fields'}
                aResult.update(result)
        elif cmd == 'pay':
            if ('uid' in frm) and ('summ' in frm) and ('tid' in frm):
                uid = int(frm["uid"].value)
                summ = float(frm["summ"].value)
                tid = frm["tid"].value
                ip = os.environ['REMOTE_ADDR']
                result = dbmanager.pay(uid, OPERATOR, summ, tid, ip)
                aResult.update(result)
            else:
                aResult.update({'result':'error', 'errno':2, 'status':'err_fields'})
        elif cmd == 'check_tid':
            if 'tid' in frm:
                tid = frm["tid"].value
                result = dbmanager.check_tid(tid)
                aResult.update(result)
            else:
                aResult.update({'result':'error', 'errno':2, 'status':'err_fields'})
        else:
            aResult.update({'result':'error', 'errno':2, 'status':'err_unknown_command'})
    else:
        aResult.update({'result':'error', 'errno':2, 'status':'err_no_command'})
        raw = aResult['datetime']+aResult['result']+SECRET
        m = hashlib.md5()
        m.update(raw)
        aResult['hash'] = m.hexdigest()
    return aResult

print "Content-type: text/json\n\n"
form = cgi.FieldStorage()

if ('hash' in form) and (check_hash(form)):
    aResult = process(form)
else:
    aResult = {'result':'error', 'errno':'5', 'status':'bad_checksum'}

print json.dumps(aResult, indent=4)
