import time
import os
from lxml import etree

uAxml = '_XML'

table = [
    ("XML files", "*.xml"),
    ("All files", "*"),
]

file_name = "/home/tbrown/Desktop/dml/all.dml"
file_name = "/home/tbrown/n/proj/BirdAtlas/PrelimDataCornell/Export_Output_8_Dissolve_Dis.shp.xml"

file_name = "/home/tbrown/Desktop/nrri.co.svg"

# file_name = g.app.gui.runOpenFileDialog(
#         title="Open", filetypes=table, defaultextension=".xml")


if not file_name:
    raise Exception("No file selected")

xml_ = etree.parse(file_name)

def get_tag(xml_node, attrib=None):
    if attrib:
        name = attrib
    else:
        name = xml_node.tag
    for k,v in xml_node.nsmap.items():
        x = "{%s}" % v
        r = k+":" if k else ""
        if name.startswith(x):
            name = name.replace(x, r)
            break
    return name

def append_element(xml_node, to_leo_node, root_node=False):
    """handle appending ele which may be Element, Comment, ProcessingInstruction
    """
    if isinstance(xml_node, etree._Comment):
        leo_node = to_leo_node.insertAsLastChild()
        leo_node.h = "# %s" % ' '.join(xml_node.text.split())[:40]
        leo_node.b = xml_node.text
        
    elif isinstance(xml_node, etree._ProcessingInstruction):
        leo_node = to_leo_node.insertAsLastChild()
        r = [xml_node.target]+xml_node.text.split()[:40]
        leo_node.h = "? %s" % ' '.join(r)
        leo_node.b = xml_node.text
        
    elif isinstance(xml_node, etree._Element):
        leo_node = to_leo_node.insertAsLastChild()


        name = [get_tag(xml_node)]
        if xml_node.get('name'):
            name.append(xml_node.get('name'))
        if xml_node.text:  # first 9 words from text
            name.extend(xml_node.text.split(None, 10)[:9])
        
        leo_node.h = ' '.join(name)[:40]
        leo_node.b = xml_node.text
        for k in sorted(xml_node.attrib.keys()):
            if uAxml not in leo_node.v.u:
                leo_node.v.u[uAxml] = {}
            if '_edit' not in leo_node.v.u[uAxml]:
                leo_node.v.u[uAxml]['_edit'] = {}
            aname = get_tag(xml_node, k)
            leo_node.v.u[uAxml]['_edit'][aname] = xml_node.get(k)

        for xml_child in xml_node:
            append_element(xml_child, leo_node)
        

nd = p.insertAfter()
nd.h = os.path.basename(file_name)
if xml_.docinfo.xml_version:
    nd.b = '<?xml version="%s"?>\n' % xml_.docinfo.xml_version
if xml_.docinfo.encoding:
    nd.b = '<?xml version="%s" encoding="%s"?>\n' % (
    xml_.docinfo.xml_version, xml_.docinfo.encoding)

nd.b += xml_.docinfo.doctype + '\n'

root = xml_.getroot()
toplevel = root
while toplevel.getprevious() is not None:
    toplevel = toplevel.getprevious()
    
while toplevel is not None:
    append_element(toplevel, nd, root_node=True)
    toplevel = toplevel.getnext()

c.redraw()
