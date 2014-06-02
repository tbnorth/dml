import sys
from lxml import etree
import subprocess
import os
import tempfile

log = sys.stderr.write

def dotgraph(xml_, output=None, links_only=False, title=""):
    
    dot = makedot(xml_, links_only=links_only, title=title)
    
    cmd = subprocess.Popen(['dot', '-Tpdf'], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    png, err = cmd.communicate(dot)
    
    if not output:
        tfile, tname = tempfile.mkstemp(dir='/tmp')
        write = lambda x: os.write(tfile, x)
        close = lambda: os.close(tfile)
        view = True
    else:
        tname = output
        tfile = open(output, 'wb')
        write = lambda x: tfile.write(x)
        close = lambda: tfile.close()
        view = False

    write(png)
    close()
    
    if view:
        os.system('geeqie -t -r file:"%s" &' % tname)
def makedot(xml_, links_only=False, title="dd"):
    
    dom = etree.fromstring(xml_)
    dot = [
        '\ndigraph tables {',
        'graph [rankdir = RL, label="%s", labelloc=t];' % title,
        'node [shape = plaintext];',
        'subgraph cluster_key { label=Key;',
        '_tn [width=1.8, label = "TABLE NAME", filled=True, shape=box, ' \
            'style=filled, fillcolor="#ccccff", rank=max];',
        '_pk [width=1.8, label = "PRIMARY KEY", shape=box, ' \
            'fontcolor="red", rank=max];',
        '_un [width=1.8, label = "UNIQUE", filled=True, shape=box, ' \
            'style=filled, fillcolor="#ccffcc", rank=min];',
        '_op [width=1.8, label = "OPTIONAL", shape=box, ' \
            'fontcolor="#888888", rank=max];',
        '}',
        
    ]
    
    lu = {}
    
    for table in dom.xpath('//table'):
        
        skip = table.xpath('./attr[@key="dot_ignore"]')
        if skip and skip[0].text == 'true':
            continue
        
        name = table.xpath('name')[0].text.strip() + ' [label='
        
                    
        if False:  # old style
            ports = [table]
            for field in table.xpath('./field'):
                lu[field.get('id')] = "%s:%s" % (
                     table.xpath('name')[0].text.strip(), field.get('id'))
                ports.append(field)
            name += '|'.join(["<%s> %s" % (i.get('id'), i.xpath('name')[0].text.strip())
                              for i in ports]) + '"'
        else:
            ports = ['<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR><TD BGCOLOR="#ccccff">%s</TD></TR>' %
                     table.xpath('name')[0].text.strip()]
            for field in table.xpath('./field'):
                
                if (links_only and 
                    not field.get('primary_key') == 'true' and
                    not field.xpath('.//foreign_key')):
                    continue
    
                lu[field.get('id')] = "%s:%s" % (
                     table.xpath('name')[0].text.strip(), field.get('id'))
    
                fname = field.xpath('name')[0].text.strip()
                if field.get('allow_null') == 'true':
                    fname = '<FONT COLOR="#888888">%s</FONT>' % fname
                if field.get('primary_key') == 'true':
                    fname = '<FONT COLOR="red">%s</FONT>' % fname
                    
                attr = ''
                if (field.get('unique') == 'true' or
                    field.get('primary_key') == 'true'):
                    attr = ' BGCOLOR="#ccffcc"'
                    
                ports.append('<TR><TD PORT="%s"%s>%s</TD></TR>' % (
                    field.get('id'), attr, fname))
            
            name += '\n'.join(ports)
                          
            name += '</TABLE>>];'
        
        dot.append(name)
        
    for table in dom.xpath('//table'):
        
        skip = table.xpath('./attr[@key="dot_ignore"]')
        if skip and skip[0].text == 'true':
            continue
        
        name = table.xpath('name')[0].text.strip()
        for field in table.xpath('./field'):
            for fk in field.xpath('./foreign_key'):
                if fk.get('target') in lu:
                    dot.append('%s:%s -> %s' % (name, field.get('id'),
                        lu[fk.get('target')]))
                else:
                    log("No '%s' target for %s:%s\n" % (fk.get('target'), name, field.get('id')))
                    
        for m2m in table.xpath('./attr'):
            if m2m.get('key') != 'dj_m2m_target':
                continue
            # break
            dot.append('%s -> %s' % (name, m2m.text.split()[1]))
    
    dot.append('}\n')
    
    dot = '\n'.join(dot)
    
    return dot

def main():
    
    links_only = False
    if '--links-only' in sys.argv:
        links_only = True
        sys.argv.remove('--links-only')
    filename = sys.argv[1]
    if len(sys.argv) > 2:
        output = sys.argv[2]
    else:
        output = None
    dotgraph(open(filename).read(), output=output, links_only=links_only)
    
if __name__ == "__main__":
    main()
