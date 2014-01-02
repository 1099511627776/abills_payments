#!/usr/bin/python
import cgi
import cgitb
import json
import dbmanager
import os
import datetime

import hashlib
import math

cgitb.enable()

operator = 4

username = 'unipay'
pwd = 'test'


company_id = ''
company_name = ''
company_message = ''

dbmanager.init()


def process(form):
    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <response>
                    <errcode>101</errcode>
                    <errstr>Bad request format</errstr>
                </response>"""
    if(not (('USER' in form) or 'PWD' in form)):
        return aResult
    else:
        if( not (form['USER'].value == username and form['PWD'].value == pwd)):
            return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                    <response>
                                        <errcode>101</errcode>
                                        <errstr>Wrong user or password</errstr>
                                    </response>"""
    if('CMD' in form):
        cmd = form['CMD'].value
        if(cmd == 'verify'):
            if('ACCOUNT' in form):
                account = form['ACCOUNT'].value
                uid_result = dbmanager.check_user(account)
                if(uid_result['result'] == 'ok'):
                    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                    <response>
                                        <errcode>0</errcode>
                                        <errstr>User exists</errstr>
                                    </response>"""
                else:
                    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                    <response>
                                        <errcode>3</errcode>
                                        <errstr>User does not exist</errstr>
                                    </response>"""
            else:
                aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                <response>
                                    <errcode>101</errcode>
                                    <errstr>Account field is missing</errstr>
                                </response>"""
        elif((cmd == 'pay') and ('SUM' in form) and ('PAYID' in form) and ('TS' in form)):
            billid = int(form['ACCOUNT'].value)
            summ = float(form['SUM'].value)
            ip_addr = os.environ['REMOTE_ADDR']
            tid = form['PAYID'].value
            dt = datetime.datetime.strptime(form['TS'].value,'%Y-%m-%dT%H:%M:%S')
            tid_result = dbmanager.check_tid(tid)
            if tid_result['result'] != 'ok':
                result = dbmanager.pay(billid,operator,summ,tid,ip_addr,dt)
                if result['result'] == 'ok':
                    balance = dbmanager.get_operator_balance(operator)
                    balance += summ
                    dbmanager.set_operator_balance(operator,balance)
                    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                    <response>
                                        <errcode>0</errcode>
                                        <errstr>Success</errstr>
                                    </response>"""
                else:
                    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                    <response>
                                        <errcode>5</errcode>
                                        <errstr>Error while paying</errstr>
                                    </response>"""
            else:
                aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                <response>
                                    <errcode>2</errcode>
                                    <errstr>payment exists</errstr>
                                </response>"""
        elif(cmd == 'status' and ('PAYID' in form)):
            payid = form['PAYID'].value
            result = dbmanager.check_tid(payid)
            if(result['result'] == 'ok'):
                aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                <response>
                                    <errcode>0</errcode>
                                    <errstr>transaction is confirmed</errstr>
                                </response>"""
            else:
                aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                <response>
                                    <errcode>1</errcode>
                                    <errstr>Transaction internal error %(tid-count)d</errstr>
                                </response>""" % result
        elif(cmd == 'balance'):
            result = dbmanager.get_operator_balance(operator)
            aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                            <response>
                                <errcode>0</errcode>
                                <balance>%(balance)s</balance>
                                <limit>%(limit)s</limit>
                            </response>""" % {'balance':int(round(result*100,0)),'limit':0}
        else:
            aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                            <response>
                                <errcode>101</errcode>
                                <errstr>Unknown command</errstr>
                            </response>"""
    return aResult

print "Content-type: text/xml\n";
form = cgi.FieldStorage()

aResult = process(form)

print aResult
