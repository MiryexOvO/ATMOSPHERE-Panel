"""标准 TOTP 和登录网络审计，不发送账户信息到外部。"""
import base64, hashlib, hmac, ipaddress, struct, time, json
from contextlib import closing
from ..core.database import connect


def totp(secret,at=None):
    # RFC 6238：30 秒窗口，六位动态口令。
    counter=int(at if at is not None else time.time())//30
    digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',counter),hashlib.sha1).digest()
    offset=digest[-1]&15
    return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)


def matching_step(secret,code):
    if len(code)!=6 or not code.isdigit(): return None
    counter=int(time.time())//30
    return next((counter+step for step in [-1,0,1] if hmac.compare_digest(totp(secret,(counter+step)*30),code)),None)


def verify(secret,code):
    return matching_step(secret,code) is not None


def client_ip(request):
    return request.client.host if request.client else 'unknown'


def login_event(username,ip,success,user_id=None):
    try:
        address=ipaddress.ip_address(ip);network=str(ipaddress.ip_network(f'{ip}/{24 if address.version==4 else 64}',strict=False))
    except ValueError: network=ip
    now=int(time.time())
    with closing(connect()) as conn:
        known=conn.execute('SELECT 1 FROM login_events WHERE user_id=? AND success=1',(user_id,)).fetchone()
        match=conn.execute('SELECT 1 FROM login_events WHERE user_id=? AND network=? AND success=1',(user_id,network)).fetchone()
        unusual=bool(success and known and not match)
        conn.execute('INSERT INTO login_events(user_id,username,ip,network,success,unusual,created_at) VALUES(?,?,?,?,?,?,?)',(user_id,username,ip,network,int(success),int(unusual),now))
        conn.execute('INSERT INTO audit_log(user_id,action,detail,created_at) VALUES(?,?,?,?)',(user_id,'login.new-network' if unusual else 'login.success' if success else 'login.failed',json.dumps({'username':username,'ip':ip},ensure_ascii=False),now))
        if success: conn.execute('UPDATE users SET last_login=? WHERE id=?',(now,user_id))
        conn.execute('DELETE FROM login_events WHERE created_at<?',(now-90*86400,));conn.commit()
    return unusual
