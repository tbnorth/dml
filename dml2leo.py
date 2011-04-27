import time
from lxml import etree

table = [
    ("DML files", "*.dml"),
    ("All files", "*"),
]

file_name = g.app.gui.runOpenFileDialog(
        title="Open", filetypes=table, defaultextension=".dml")

if not file_name:
    raise Exception("No file selected")

dml = etree.parse(file_name).getroot()

nd = p.insertAfter()

if dml.get('db_schema'):
    nd.v.u['dml'] = {'_edit':{}}
    nd.v.u['dml']['_edit']['db_schema'] = dml.get('db_schema')

nd.h = 'DML schema'
nd.b = """DML imported from '%s'
on %s
""" % (file_name, time.strftime("%Y%m%d %H:%M:%S"))

desc = dml.xpath('./description')
if desc and desc[0].text and desc[0].text.strip():
    nd.b += '\n'+desc[0].text.strip()+'\n'
            
# pass one, make fields
tf2n = {}
for table in dml.xpath('./table'):
    tn = nd.insertAsLastChild()
    tname = table.get('name')
    tn.h = tname
    for field in table.xpath('./field'):
        fn = tn.insertAsLastChild()
        fname = field.get('name')
        fn.h = fname
        desc = field.xpath('./description')
        if desc and desc[0].text and desc[0].text.strip():
            fn.b = desc[0].text.strip()+'\n\n'
            
        fn.v.u['dml'] = {'_edit':{}}

        for i in 'type', 'primary_key', 'unique', 'editable', 'nullable':
            if field.get(i):
                # fn.b += ':%s: %s\n' % (i, field.get(i))
                fn.v.u['dml']['_edit'][i] = field.get(i)
        
        tf2n[tname+fname] = fn.v
        
blc = c.backlinkController
        
# pass two, make links
for table in dml.xpath('./table'):
    tname = table.get('name')
    for field in table.xpath('./field'):
        
        fname = field.get('name')
        for fk in field.xpath('./foreign_key'):
            ofield = dml.xpath('//field[@id="%s"]'%fk.get('target'))[0]
            otable = ofield.getparent()
            onode = tf2n[otable.get('name')+ofield.get('name')]
            node = tf2n[tname+fname]
            blc.vlink(node, onode)

c.redraw()
