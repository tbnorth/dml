from lxml.builder import E
from lxml import etree
import time

# make map from linked node's ids to their vnodes
vnode = {}
for nd in c.all_positions():
    vnode[nd.v.gnx] = nd.v

dml = E.dml()

try:
    dml.set('db_schema', p.v.u['dml']['_edit']['db_schema'])
except KeyError:
    pass

if p.b.strip():
    dml.append(E.description(p.b.strip()))

for tnode in p.children():
    table = E.table(name=tnode.h, id='_tbl_'+tnode.h)
    dml.append(table)
    if tnode.b.strip():
        table.append(E.description(tnode.b.strip()))
    for fnode in tnode.children():
        field = E.field(name=fnode.h, id='_fld_'+tnode.h+'_'+fnode.h)
        table.append(field)
        if fnode.b.strip():
            field.append(E.description(fnode.b.strip()))
        for i in 'type', 'primary_key', 'unique', 'editable', 'nullable':
            try:
                field.set(i, fnode.v.u['dml']['_edit'][i])
            except KeyError:
                pass
        try:
            links = fnode.v.u['_bklnk']['links']
        except KeyError:
            links = []
        for l in links:
            if l[0] != 'S':  # we're not the source
                continue
            dest = vnode[l[1]]
            field.append(E.foreign_key(target='_fld_'+dest.directParents()[0].h+'_'+dest.h))
                
c.leo_screen.show(etree.tostring(dml, pretty_print=True), 'dml', plain=True)

table = [
    ("DML files", "*.dml"),
    ("All files", "*"),
]
file_name = g.app.gui.runSaveFileDialog(
        title="Open", filetypes=table, defaultextension=".dml")
if not file_name:
    raise Exception("No file selected")
desc = dml.xpath('./description')
msg = """DML exported to '%s'
on %s
""" % (file_name, time.strftime("%Y%m%d %H:%M:%S"))

if desc:
    desc[0].text = msg+'\n' + desc[0].text
else:
    dml.append(E.description(msg))
     
open(file_name, 'w').write(etree.tostring(dml, pretty_print=True))
