"""
Read postgres data from one source and write it to another,
in a manner which will gloss over type differences,
field order, and missing fields.

python sql2sql postgres://server0.etc postgres://server1.etc 
"""

from optparse import OptionParser

import psycopg2

from parse_pg_uri import parsePosturl

"""
python sql2sql.py \
  postgres://tbrown:frogspit@127.0.0.1:25432/nrgisl01.glei_1_orig.v_locations \
  postgres://tbrown:frogspit@127.0.0.1:25432/nrgisl01.glei_1.v_locations
"""

def make_parser():
    
    parser = OptionParser()
    
    parser.add_option("--drop", action='append', default=[],
                  help="Drop field (repeat and/or comma sep.)")
    parser.add_option("--map", action='append', default=[],
                  help="Map from src to dst, sname:dname (repeat and/or comma sep.)")
    parser.add_option("--list-null", action='store_true', default=False,
                  help="Scan fields in src for null values")
    parser.add_option("--null-to-empty", action='store_true', default=False,
                  help="Translate null values in text fields to ''")
    parser.add_option("--quote-fields", action='store_true', default=False,
                  help="Quote fields to allow bad names, becomes case sensitive.")

    return parser
def main():
    
    opt, arg = make_parser().parse_args()
    
    sources = []
    
    for uri in arg[:2]:
        
        d = {'uri': uri}
        sources.append(d)
        d['descrip'] = parsePosturl(uri)
        d['con'] = psycopg2.connect(d['descrip']['connect2'])
        d['cur'] = d['con'].cursor()
        d['cur'].execute('select * from %s limit 0'%d['descrip']['s.t'])
        d['fields'] = dict([(i[0],i[1]) for i in d['cur'].description])
    
    src, dst = sources

    fmap = dict([(i,i) for i in dst['fields'] if i in src['fields']])
    
    for i in opt.map:
        for j in i.split(','):
            f,t = j.strip().split(':')
            if t not in dst['fields']:
                print("Can't map '%s' to '%s', '%s' not in destination" %
                    (f, t, t))
                continue
            if f not in src['fields']:
                print("Can't map '%s' to '%s', '%s' not in source" %
                    (f, t, f))
                continue
            fmap[f] = t

    for i in opt.drop:
        for j in i.split(','):
            if j.strip() in fmap:
                del fmap[j.strip()]
                print("Dropped '%'" % j.strip())
            else:
                print("Can't drop '%', not present in source" % j.strip())
                
    sflds = []
    dflds = []
    quote = '"' if opt.quote_fields else ''
    for f,t in fmap.iteritems():
        assert f in src['fields']
        assert t in dst['fields']
        if opt.null_to_empty and src['fields'][f] == 25:
            sflds.append("coalesce(%s%s%s,'')" % (quote,f,quote))
        else:
            sflds.append(quote+f+quote)
        dflds.append(quote+t+quote)
        print("%s -> %s" % (quote+t+quote, quote+f+quote))
    
    slots = ','.join(['%s']*len(dflds))
    
    q0 = "select %s from %s" % (','.join(sflds), src['descrip']['s.t'])
    q1 = "insert into %s (%s) values (%s)" % (
        dst['descrip']['s.t'], ','.join(dflds), slots)
    
    print(q0)
    
    src['cur'].execute(q0)
    
    if opt.list_null:
        null = set()
        cnt = 0
        for i in src['cur'].fetchall():
            cnt += 1
            for fld, value in zip(sflds, i):
                if value is None:
                    null.add(fld)
        print("\nFields with nulls (scanned %d records)\n" % cnt)
        for i in sorted(null):
            print('%s (%r)' % (i, src['fields'][i.strip('"')]))
        print('')
        return
    
    print(q1)
    
    for i in src['cur'].fetchall():
        
        dst['cur'].execute(q1, i)

    dst['con'].commit()
if __name__ == '__main__':
    main()
