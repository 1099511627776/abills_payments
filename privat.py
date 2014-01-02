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

operator = 15

company_id = ''
company_name = ''
company_message = ''

dbmanager.init()

####errno : 1 - unknown user
####errno : 2 - error making payment
####errno : 3 - transaction exists
####errno : 4 - transaction not exists
####errno : 5 - bad chacksum
####errno : 6 - bad request format

def process(form):
    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <errorResponse>
                    <code>1</code>
                    <message>Bad request format</message>
                </errorResponse>"""
    if('action' in form):
        if(form['action'].value == 'bill_search'):
            if('bill_identifier' in form):
                uid = int(form['bill_identifier'].value)
                uid_result = dbmanager.check_user(uid)
                if(uid_result['result'] == 'ok'):
                    deposit = dbmanager.get_deposit2(uid)
                    if deposit < 0:
                        deposit = -deposit
                    else:
                        deposit = 0
                    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                        <ResponseDebt>
                            <debtPayPack fio="%(fio)s" bill_identifier="%(uid)s" address="%(address)s">
                            <service>
                            <ks service_code="1" service="%(company_name)" company_code="%(company_code)"/>
                            <payer ls="%(uid)s"/>
                            <debt amount_to_pay="%(deposit)2g" />
                            <message>%(company_message)s</message>
                            </service>
                            </debtPayPack>
                        </ResponseDebt>""" % {'login':uid_result['id'],'address':uid_result['addr'],'fio':uid_result['fio'],'uid':uid,'deposit':math.ceil(deposit),'company_name':company_name,'company_code':company_code,'company_message':company_message}
                else:
                    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                        <ResponseDebt>
                        <errorResponse>
                            <code>1</code>
                            <message>Unknown user</message>
                        </errorResponse>
                        </ResponseDebt>"""
            else:
                aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                    <ResponseDebt>
                    <errorResponse>
                        <code>1</code>
                        <message>Unknown user</message>
                    </errorResponse>
                    </ResponseDebt>"""
        elif(form['action'].value == 'bill_input'):
            if ('bill_identifier' in form) and ('summ' in form) and ('pkey' in form):
                uid = int(form['bill_identifier'].value)
                summ = float(form['summ'].value)
                pkey = str(form['pkey'].value)
                ip = os.environ['REMOTE_ADDR']
                datt = form['date']
                check_double = dbmanager.check_tid(pkey)
                if('errno' in check_double and check_double['errno'] == 3):
                    result = dbmanager.pay(uid,operator,summ,pkey,ip,datt)
                    if(result['result'] == 'ok'):
                        aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                <ResponseExtInputPay>
                                <extInputPay>
                                    <inner_ref>%(pkey)s</inner_ref>
                                </extInputPay>
                            </ResponseExtInputPay>""" % {'pkey' : pkey }
                    else:
                        aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                <ResponseExtInputPay>
                                <errorResponse>
                                <code>99</code>
                                <message>$(status)s</message>
                                </errorResponse>
                                </ResponseExtInputPay>
                            """ % result
                else:
                    aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                            <ResponseExtInputPay>
                            <errorResponse>
                            <code>99</code>
                            <message>Double check</message>
                            </errorResponse>
                            </ResponseExtInputPay>"""
            else:
                aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                        <ResponseExtInputPay>
                        <errorResponse>
                            <code>1</code>
                            <message>Bad request (no sum or bill_identifier)</message>
                        </errorResponse>
                        </ResponseExtInputPay>"""
        else:
            aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                    <ResponseExtInputPay>
                    <errorResponse>
                        <code>1</code>
                        <message>Bad action</message>
                    </errorResponse>
                    </ResponseExtInputPay>"""
    else:
        aResult = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                    <ResponseExtInputPay>
                    <errorResponse>
                        <code>1</code>
                        <message>Bad request format (no action field)</message>
                    </errorResponse>
                    </ResponseExtInputPay>"""
    return aResult

print "Content-type: text/xml\n";
form = cgi.FieldStorage()

aResult = process(form)

print aResult
