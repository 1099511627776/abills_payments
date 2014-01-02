"""Raw operations on abills database"""

import MySQLdb as mdb
import datetime

_CFG = {
    'host':'127.0.0.1',
    'user':'payments',
    'pwd':'password',
    'db':'abills'
}
_DB = None

def init():
    """Init database conection"""
    global _DB
    _DB = mdb.connect(_CFG['host'], _CFG['user'], _CFG['pwd'], _CFG['db'])
    cur = _DB.cursor()
    cur.execute("SET NAMES utf8")
    cur.execute("SET AUTOCOMMIT=1")
    return cur.fetchone()

def check_user(uid):
    """Checking users + return some information"""
    cur = _DB.cursor()
    sql = """
    SELECT 
        id,
        u.uid,
        gid,
        fio,
        phone,
        concat(address_street,',',address_build,',',address_flat)
    FROM users u 
        INNER JOIN users_pi upi ON u.uid = upi.uid WHERE u.bill_id = %s """
    if cur.execute(sql, uid) != 0:
        data = cur.fetchone()
        return {
            'result':'ok',
            'id':data[0],
            'uid':data[1],
            'gid':data[2],
            'fio':data[3],
            'phone':data[4],
            'addr':data[5]
        }
    else:
        return {'result':'error', 'errno':1, 'status':'unknown user'}

def get_deposit(uid):
    """Get user deposit by UID"""
    sql = "SELECT deposit FROM bills WHERE uid = %s"
    cur = _DB.cursor()
    cur.execute(sql, uid)
    data = cur.fetchone()
    return data[0]

def get_deposit2(billid):
    """Get user deposit by BILL_ID"""
    sql = "SELECT deposit FROM bills WHERE id = %s"
    cur = _DB.cursor()
    cur.execute(sql, billid)
    data = cur.fetchone()
    return data[0]

def set_deposit(uid, deposit):
    """Set user deposit by UID"""
    sql = "UPDATE bills SET deposit = %s WHERE id = %s"
    cur = _DB.cursor()
    return cur.execute(sql, (deposit, uid))

def get_operator_balance(aid):
    """ Operator balance for Unipay protocol. The data is stored in email field of the DB"""
    sql = "SELECT email FROM admins WHERE aid = %s "
    cur = _DB.cursor()
    cur.execute(sql, aid)
    data = cur.fetchone()
    return float(data[0]) if data[0] != '' else 0

def set_operator_balance(aid, balance):
    """ Updates operator balance for Unipay protocol. The data is stored in email field of the DB"""
    sql = "UPDATE admins SET email = %s WHERE aid = %s "
    cur = _DB.cursor()
    cur.execute(sql, (str(balance), aid, ))

def get_uid(billid):
    """Get user UID by BILL_ID"""
    sql = "SELECT uid FROM users WHERE bill_id = %s"
    cur = _DB.cursor()
    cur.execute(sql, billid)
    data = cur.fetchone()
    return data[0]

def check_tid(tid, prefix="tr_id:"):
    """Check transaction """
    sql = """ SELECT count(*) FROM payments WHERE ext_id = %s """
    cur = _DB.cursor()
    if cur.execute(sql, prefix+str(tid)) != 0:
        data = cur.fetchone()
        if data[0] != 0:
            return {'result':'ok', 'tid-count':data[0]}
        else:
            return {'result':'error', 'tid-count':data[0], 'errno':3}
    else:
        return {'result':'erorr', 'status':'db_error', 'errno':2}

def pay(billid, operator, summ, tid, ip_addr, datt=None):
    """Direct pay of 'sum' by 'operator' to 'bill_id' from 'ip'"""
    uid = get_uid(billid)
    deposit = get_deposit2(billid)
    if datt == None:
        pay_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        pay_date = datt
    sql = """INSERT INTO payments(bill_id,uid,date,sum,amount,last_deposit,
                                  ext_id,inner_describe,aid,ip,reg_date)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, INET_ATON(%s), %s)"""
    cur = _DB.cursor()
    res = cur.execute(sql, (billid, uid, pay_date, summ, summ, deposit,
                            "tr_id:"+str(tid), "", operator, ip_addr, pay_date))
    if res == 1:
        res = set_deposit(billid, deposit + summ)
        if res == 1:
            return {'result':'ok'}
        else:
            return {'result':'error', 'status':'err_depo', 'errno':2}
    else:
        return {'result':'error', 'status':'fatal', 'errno':2}

def pay_order(billid, operator, summ, tid, ip_addr, datt=None):
    """2 Phase pay: Makes pay order to 'bill_id' by 'operator' of
    'summ' transaction - 'tid' (required)"""
    uid = get_uid(billid)
    deposit = get_deposit2(billid)
    if datt == None:
        pay_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        pay_date = datt
    sql = """INSERT INTO payments(bill_id,uid,date,sum,amount,last_deposit,
                                  ext_id,inner_describe,aid,ip,reg_date)
              values (%s, %s, %s, %s, %s, %s, %s, %s, %s, INET_ATON(%s), %s)"""
    cur = _DB.cursor()
    if cur.execute(sql, (billid, uid, pay_date, 0, 0, deposit,
                        "tr_id:"+str(tid), summ, operator, ip_addr, pay_date)) == 1:
        return {'result':'ok'}
    else:
        return {'result':'error', 'status':'fatal', 'errno':2}

def delete_order(order_id):
    """Rollbacks payment with order_id"""
    sql = "DELETE FROM payments WHERE ext_id = %s"
    cur = _DB.cursor()
    cur.execute(sql, ("pending_id:"+str(order_id), ))

def confirm_order(order_id):
    """Commit order 'order_id'"""
    sql = "SELECT inner_describe,date,bill_id,sum FROM payments WHERE ext_id = %s"
    cur = _DB.cursor()
    dbl = check_tid(order_id)
    if dbl['result'] == 'ok':
        if cur.execute(sql, "tr_id:"+str(order_id)) != 0:
            row = cur.fetchone()
            summ = float(row[0])
            date = row[1]
            billid = row[2]
            real_sum = float(row[3])
            if real_sum == 0:
                sql = "UPDATE payments SET sum = %s, amount = %s WHERE ext_id = %s"
                res = cur.execute(sql, (summ, summ, "tr_id:"+str(order_id), ))
                if cur.rowcount == 1:
                    deposit = get_deposit2(billid)
                    res = set_deposit(billid, deposit + summ)
                    return {'result':'ok', 'date':date, 'status':'ok'}
                else:
                    return {'result':'error', 'status':'result == '+str(res), 'date':date}
            else:
                return {'result':'ok', 'date':date, 'status':'already confimed'}
        else:
            return {'result':'error', 'status':'no transaction', 'date':''}
    else:
        return {'result':'error', 'status':'tid check error', 'date':''}

#init()
#uid = 10
#data = check_user(uid)
#print "checkuser: ",data
#print "deposit", get_deposit(uid)
#print "deposit", get_billid(uid)
#pay(uid,2,100.01,32113,'192.168.0.1')
#print set_deposit(uid,100.01)
