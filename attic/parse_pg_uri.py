"""
"""

def psplit(s, d, second=False):
    """for parsing "a", "a.b", "b.a" where b is optional

    return s.split(d) if d in s, else s,'' if not second, else '',s"""
    if d in s:
        return s.split(d,1)
    else:
        if not second:
            return s, ''
        else:
            return '', s

def parsePosturl(URL):
    """make a dict from URLs like 
    postgres://user:password@host:port/db.schema.tablename

    keys:

    * database
    * user
    * password
    * table
    * schema
    * port
    * host
    * hostonly (host includes port if present)
    * s.t (table or schema.table if schema present)
    * connect (a dict of the database user password host if provided)
    * connect2 (a "dbname=foo user=bar" style connect string)
    """

    tmp = URL[11:].split('/')
    while len(tmp) < 2: tmp.insert(0,'')

    ans = {}

    usrpwhopt, ans['d.s.t'] = tmp

    ans['user'], ans['host'] = psplit(usrpwhopt, '@', True)
    ans['hostonly'], ans['port'] = psplit(ans['host'], ':')
    ans['user'], ans['password'] = psplit(ans['user'], ':')
    ans['database'], ans['s.t'] = psplit(ans['d.s.t'], '.')
    ans['schema'], ans['table']  = psplit(ans['s.t'], '.', True)
    connectKeys = [  # columns are connect2 key, connect2 source, and connect entries
        ('dbname',   'database', 'database'),
        ('host',     'hostonly', 'host'),
        ('port',     'port',     'port'),
        ('user',     'user',     'user'),
        ('password', 'password', 'password'),
    ]
    ans['connect'] = dict([(x,ans[x]) for k,v,x in connectKeys if ans[x]])
    ans['connect']['host'] = ans['hostonly'] 
    ans['connect2'] = dict([(k,ans[v]) for k,v,x in connectKeys if ans[v]])
    if ans['connect2']:
        ans['connect2'] = ' '.join(['%s=%s' % (k,v) 
                                  for k,v in ans['connect2'].iteritems()])
    else:
        ans['connect2'] = ''

    for i in ans['connect']:
        if isinstance(ans['connect'][i], unicode):
            ans['connect'][i] = str(ans['connect'][i])

    return ans
