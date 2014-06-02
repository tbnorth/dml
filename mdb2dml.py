"""
mdb2dml.py - Generate DML from an Access .mdb using mdb-tools via subprocess

Terry Brown, Terry_N_Brown@yahoo.com, Mon Jul 22 14:24:41 2013
"""

import os
import sys
import subprocess
from pprint import pprint
from lxml import etree
from lxml.builder import E
from collections import OrderedDict

def norm(s):
    s = ''.join(i if i.isalnum() else '_' for i in s)
    return '_'.join(s.lower().split())

def get_tbl_fld_typ(mdb):
    """get_tbl_fld_typ - Return a dict to look up types from table and field
    name using access format names, the default output from mdb-schema

    :Parameters:
    - `mdb`: filename of .mdb file
    """

    cmd = ['mdb-schema', mdb]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    lines, dummy = proc.communicate()
    table = {}
    for line in lines.split('\n'):
        if line.startswith('CREATE TABLE ['):
            table_name = line.split('[')[1].strip(']')
            table[table_name] = {'field':{}}
        if line.startswith('\t['):
            field_name = line.split('[')[1].split(']')[0]
            table[table_name]['field'][field_name] = line.split()[1].strip(',')
    return table

def main():
    
    mdb = sys.argv[1]
    
    tbl_fld_typ = get_tbl_fld_typ(mdb)
    
    cmd = ['mdb-tables', mdb]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    table_names, dummy = proc.communicate()
    table_names = table_names.split()
    
    """ mdp-prop output is 
    name: nrricode
        DecimalPlaces: 255
        ColumnWidth: 960
        ColumnOrder: 0
        Required: no
        ColumnHidden: no
        Description: numerical code for bird species; see 'nrri_bird_codes' look
        DisplayControl: 109
    (tab indentation)
    """
    
    table = OrderedDict()
    
    for table_name in table_names:
        cmd = ['mdb-prop', mdb, table_name]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        props, dummy = proc.communicate()
        
        table[table_name] = {'field': OrderedDict()}
        for line in props.split('\n'):
            if line.startswith('name: '):
                field_name = '_'.join(line.split()[1:])
                table[table_name]['field'][field_name] = OrderedDict()
                table_lu = tbl_fld_typ.get(table_name)
                if table_lu:
                    field_lu = tbl_fld_typ[table_name]['field'].get(field_name)
                    if field_lu:
                        table[table_name]['field'][field_name]['_TYPE'] = field_lu
            if line.startswith('\t'):
                prop_name = line.split()[0].strip(':')
                table[table_name]['field'][field_name][prop_name] = ' '.join(
                    line.split()[1:])

    dml = E.dml()

    for table_name in table:
        
        if table_name[0] == '(':
            continue
        
        Table = E.table(E.name(norm(table_name)), id=norm('_tbl_'+table_name))
        
        field = table[table_name]['field']
        for field_name in field:
            if field_name[0] == '(':
                continue
            descrip = field[field_name].get('Description') or 'NO DESCRIPTION'
            descrip = unicode(descrip.decode('utf-8'))
            Field = E.field(
                E.name(norm(field_name)),
                E.description(descrip),
                E.type(field[field_name].get('_TYPE', 'UNKNOWN')),
                id="_fld_%s_%s" % (norm(table_name), norm(field_name)),
                primary_key="false",
                unique="false",
                allow_null="false",
            )

            Table.append(Field)
            
        
        dml.append(Table)
        
    print etree.tostring(dml, pretty_print=True)
        
        


if __name__ == '__main__':
    main()
