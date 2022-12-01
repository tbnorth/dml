"""
reconcile_lookup.py - compare lookup tables in different DBs / schemas

Terry Brown, Terry_N_Brown@yahoo.com, Tue Aug  6 11:58:32 2013
"""

import os
import sys
from collections import namedtuple
import textwrap

import psycopg2

CompTable = namedtuple("CompTable", "host port db user pw table pk match_fields")

to_compare = [
    # master
    CompTable("127.0.0.1", 15432, "nrgisl01", 'tbrown', 'frogspit',
        "glrimon.b_taxa", "taxa", ["code"]),
    # copies
    CompTable("127.0.0.1", 15432, "nrgisl01", 'tbrown', 'frogspit',
        "mnbba.mncode", "mncode", ["abbrev"]),
    CompTable("127.0.0.1", 15432, "nrgisl01", 'tbrown', 'frogspit',
        "glrig2.b_taxa", "taxa", ["code"]),
]
_compare = [
    # master
    CompTable("127.0.0.1", 15432, "nrgisl01", 'tbrown', 'frogspit',
        "glrimon.a_taxa", "taxa", ["code"]),
    # copies
    CompTable("127.0.0.1", 15432, "nrgisl01", 'tbrown', 'frogspit',
        "glrig2.a_taxa", "taxa", ["code"]),
]
_compare = [
    # master
    CompTable("127.0.0.1", 15432, "nrgisl01", 'tbrown', 'frogspit',
        "glrimon.v_taxa", "taxa", ["name"]),
    # copies
    CompTable("127.0.0.1", 15432, "nrgisl01", 'tbrown', 'frogspit',
        "glrig2.v_taxa", "taxa", ["name"]),
]

def show_table(name, table):
    if len(table) == 0:
        print("No %s" % name)
    else:
        print("%d %s" % (len(table), name))
        for i in table:
            print i

def main():
    
    db = []
    
    for n, ct in enumerate(to_compare):
        con = psycopg2.connect("dbname=%s host=%s user=%s port=%s password=%s" %
            (ct.db, ct.host, ct.user, ct.port, ct.pw))
        cur = con.cursor()
        cur.execute("select %s, %s from %s" %
            (ct.pk, ', '.join(ct.match_fields), ct.table))
        db.append({'n': n, 'ct': ct, 'con': con, 'cur': cur,
            'data': dict((i[0], i[1:]) for i in cur.fetchall())})
        print("%d %s %d records" % (n, ct.table, len(db[n]['data'])))
        
    base = db[0]
    for ct in db[1:]:
        
        missing = []
        match = []
        mismatch = []
        extra = []
        
        for i in base['data']:
            if i not in ct['data']:
                missing.append((i,)+base['data'][i])
            elif base['data'][i] != ct['data'][i]:
                mismatch.append((i,)+base['data'][i])
                mismatch.append((i,)+ct['data'][i])
            else:
                match.append((i,)+ct['data'][i])
                
        for i in ct['data']:
            if i not in base['data']:
                extra.append((i,)+ct['data'][i])
                
        print("%s %s\n%d match" % (ct['ct'].db, ct['ct'].table, len(match)))
        
        show_table("missing", missing)
        if missing:
            b = base['ct']
            c = ct['ct']
            print('\n'.join(textwrap.wrap(
                "insert into %s select * from %s where not exists (select 1 from %s where %s.%s = %s.%s);" % (
                c.table, b.table,
                c.table, c.table, c.pk,
                b.table, b.pk))))
                
        show_table("mismatch", mismatch)
        if mismatch:
            pass
            
        show_table("extra", extra)
        if extra:
            c = base['ct']
            b = ct['ct']
            print('\n'.join(textwrap.wrap(
                "insert into %s select * from %s where not exists (select 1 from %s where %s.%s = %s.%s);" % (
                c.table, b.table,
                c.table, c.table, c.pk,
                b.table, b.pk))))

         
              


if __name__ == '__main__':
    main()
