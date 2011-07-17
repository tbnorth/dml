# encoding: utf-8

"""Read .dia or .dml representation of db and write other formats

.dia is deprecated

Round trip / unchanged output testing:
  # cp ~/Desktop/Proj/BirdAtlas/bbadb2.dia test.dia
  python dia2py.py --mode=dml test.dia >a.dml
  python dia2py.py --mode=dml a.dml >b.dml
  python dia2py.py --mode=django test.dia >a
  python dia2py.py --mode=django a.dml >b
  md5sum a.dml b.dml a b
  7f1890bcad93325a1e518616ad705f33  a.dml
  7f1890bcad93325a1e518616ad705f33  b.dml
  30e34420e3e590ec6bbb8ad35c7149f9  a
  30e34420e3e590ec6bbb8ad35c7149f9  b

"""

"""Convert dia *Database* diagrams to python data structures / SQL

tedia2sql converts dia *UML* to sql, which is different

dia Database table connections are numbered from 0, with two per attribute,
starting at 12 for the left side of the first attribute
(0-11 are just points on the box, 5 on top, two either side of the
heading, and 5 on the bottom)
"""

from lxml import etree
from lxml.builder import E

import sys
import textwrap
import optparse
import time
class Table(object):

    def __init__(self):
        self.fields = []
        self.field = {}
        self.c2f = {}  # connection number to field name
        self._is_many_to_many = None
        self.attr = {}
        self.validators = []
    def __repr__(self):
        
        out = ['\nTABLE '+self.name]
        # FIXME attributes, description
        for i in self.fields:
            out.append(repr(self.field[i]))
        return '\n'.join(out)
    def is_many_to_many(self):

        if self._is_many_to_many is None:
            self._is_many_to_many = (
              '!M2M' not in self.comment and
              not ('is_m2m' in self.attr and not any_to_bool(self.attr['is_m2m'])) and
              (
                ((2 <= len(self.fields) <= 3) and
                all(self.field[f].type == 'ID' for f in self.fields))
                or
                'M2M' in self.comment 
                or
                'is_m2m' in self.attr and any_to_bool(self.attr['is_m2m'])
              )
            )

        return self._is_many_to_many
class Field(object):

    def __init__(self, table):
        self.table = table
        self.foreign_key = None
        self.foreign_key_external = False
        self.referers = []  # fields for which this field is a foreign key
        self.primary_key = False
        self.unique = False
        self.allow_null = False
        self.name = '*UNNAMED FIELD*'
        self.comment = ''
        self.editable = True
        self.m2m_link = False
        self.attr = {}
        self.validators = []
    def __repr__(self):
        
        out = ['  FIELD '+self.name]
        if self.m2m_link:
            out = ['  FIELD -> '+self.name]
        # FIXME attributes, description
        if self.foreign_key and not self.foreign_key_external:
            out.append('    -> %s.%s'%(self.foreign_key.table.name, 
                                       self.foreign_key.name))
        for i in self.referers:
            out.append('    <- %s.%s'%(i.table.name, i.name))
        return '\n'.join(out)
    def is_many_to_many(self):

        ans = (
            self.foreign_key and
            not self.foreign_key_external and
            self.foreign_key.table.is_many_to_many() and
            self.type == 'ID' and
            self.foreign_key.table.fields.index(self.name) < 3
        )

        # sys.stderr.write(repr((ans, self.table.name, self.name, self.table.fields)) + '\n')

        return ans
class OutputCollector(object):

    def __init__(self, *args, **kwargs):
        
        self._output = []
        
    def emit(self, *args):
        
        if args and args[-1] is None:
            self._output.append(' '.join(args[:-1]))
        else:
            self._output.append(' '.join(args)+'\n')
        
    def result(self):
        
        return ''.join(self._output)
class RstOut(OutputCollector):
    def start(self, schema):
        self.emit('.. contents::\n')

    '''
    <style>
    blockquote { font-style: italic; margin: 0 0 0 2em; padding: 0; }
    div.line-block { margin: 0; padding: 0 }
    </style>
    '''
    def stop(self, schema):
        pass
    def start_table(self, table):
        self.emit(table.name)
        self.emit("="*len(table.name)+'\n')

    def end_table(self, table):
        self.emit()
    def show_field(self, field):
        
        ans = ['| ']
        if field.primary_key:
            ans.append('* ')
        ans.append(field.name)
        if field.foreign_key:
            ans.append('▷%s.%s' % (field.foreign_key.table.name, field.foreign_key.name))
        for f in field.referers:
            ans.append('◁%s.%s' % (f.table.name, f.name))       
        self.emit(*ans)
        
        if field.comment.strip():
            self.emit()
            for l in field.comment.split('\n'):
                self.emit('  %s' % l)
            self.emit()
    def show_link(self, from_table, from_field, to_table, to_field):
        pass
class DMLOut(OutputCollector):

    def __init__(self, *args, **kwargs):
        OutputCollector.__init__(self, *args, **kwargs)
        self.db_schema = kwargs.get('db_schema', '')

    def start(self, schema):
        
        self.dom = E.dml()
        
        self.dom.append(E.name(schema.get('_name', '') or ''))
        if '_description' in schema:
            self.dom.append(E.description(schema['_description'] or ''))
            
        for i in schema.get('_attr', {}):
            self.dom.append(E.attr(schema['_attr'][i], key=i))
        
        log = E.log(
                E.log_entry("written by dia2py",
                    date=time.strftime("%Y%m%d %H:%M:%S")))
        self.dom.append(log)
        
        if '_log' in schema:
            for i in schema['_log']:
                log.append(E.log_entry(i[1], date=i[0]))   
        
        if schema.get('_db_schema'):
            self.dom.append(E.attr(schema.get('_db_schema'), key='db_namespace'))
    def stop(self, schema):
        self.emit(etree.tostring(self.dom, pretty_print=True))
    def start_table(self, table):
        self.table = E.table(E.name(table.name))
        self.dom.append(self.table)
        if table.comment.strip():
            self.table.append(E.description(table.comment))
        self.table.set('id', '_tbl_%s' % table.name)
        for i in table.attr:
            self.table.append(E.attr(table.attr[i], key=i))
    def end_table(self, table):
        pass
    def show_field(self, field):
        
        if field.m2m_link:
            return
        
        fld = E.field(
            E.name(field.name),
            E.description(field.comment),
            E.type(field.type),
        )
        self.table.append(fld)
        atr = fld.attrib
        
        if field.foreign_key:
            fld.append(E.foreign_key(target='_fld_%s_%s' % (
                field.foreign_key.table.name, field.foreign_key.name)))

        atr['id'] = '_fld_%s_%s' % (field.table.name, field.name)
        for i in 'primary_key', 'unique':
            atr[i] = str(getattr(field, i)).lower()

        atr['allow_null'] = 'true' if field.allow_null else 'false'
            
        if not field.editable and 'dj_editable' not in field.attr:
            fld.append(E.attr('false', key='dj_editable'))

        for i in field.attr:
            fld.append(E.attr(field.attr[i], key=i))
    def show_link(self, from_table, from_field, to_table, to_field):
        pass

class oldDMLOut(OutputCollector):

    def __init__(self, *args, **kwargs):
        OutputCollector.__init__(self, *args, **kwargs)
        self.db_schema = kwargs.get('db_schema', '')

    def start(self, schema):
        self.dom = E.dml()
        if schema.get('_db_schema'):
            self.dom.set('db_schema', schema.get('_db_schema'))
    def stop(self, schema):
        self.emit(etree.tostring(self.dom, pretty_print=True))
    def start_table(self, table):
        self.table = E.table()
        self.dom.append(self.table)
        atr = self.table.attrib
        atr['id'] = '_tbl_%s' % table.name
        atr['name'] = table.name
    def end_table(self, table):
        pass
    def show_field(self, field):
        
        fld = E.field()
        self.table.append(fld)
        atr = fld.attrib
        
        atr['id'] = '_fld_%s_%s' % (field.table.name, field.name)
        for i in 'name', 'type', 'primary_key', 'allow_null', 'editable', 'unique':
            atr[i] = str(getattr(field, i))

        if field.foreign_key:
            fld.append(E.foreign_key(target='_fld_%s_%s' % (
                field.foreign_key.table.name, field.foreign_key.name)))
                
        fld.append(E.description(field.comment))
    def show_link(self, from_table, from_field, to_table, to_field):
        pass

class SimpleOut(OutputCollector):
    """Deprecated - use RstOut"""
    def start(self, schema):

        self.emit('SimpleOut is deprecated in favor of RstOut')
    def stop(self, schema):

        self.emit('SimpleOut is deprecated in favor of RstOut')
    def start_table(self, table):
        self.emit(table.name)
    def end_table(self, table):
        pass
    def show_field(self, field):
        self.emit('  '+('*' if field.primary_key else ' ')+field.name)

    def show_link(self, from_table, from_field, to_table, to_field):
        pass
class SQLOut(OutputCollector):
    def __init__(self, *args, **kwargs):
        
        OutputCollector.__init__(self, *args, **kwargs)
        self.db_schema = kwargs.get('db_schema', '')

        self.first_field = True

        self.db_schema = db_schema

        self.foreign_key_names = []  # avoid duplicating foreign key names
    def _type_map(self, field):
        if field.primary_key:
            return 'bigserial primary key'
        elif field.type == 'ID':
            return 'bigint'
        else:
            return field.type

    def start(self, schema):
        self.emit("\set ON_ERROR_STOP 1;")
    def start_table(self, table):
        self.first_field = True
        self.emit("drop table if exists %s cascade;" % table.name)
        self.emit("create table %s(" % table.name)

    def end_table(self, table):
        self.emit()
        self.emit(");")

        if table.comment:
            self.emit("comment on table %s is '%s';" % 
                (table.name, table.comment.replace("'", "''")))

        for f in table.fields:
            F = table.field[f]
            if F.comment:
                self.emit("comment on column %s.%s is '%s';" % (table.name, F.name,
                    F.comment.replace("'", "''")))
    def show_field(self, field):
        if not self.first_field:
            self.emit(',')
        self.first_field = False
        self.emit('  ', field.name, self._type_map(field), None)
        if field.unique:
            self.emit('unique', None)
        if not field.allow_null:
            self.emit('not null', None)

    def show_link(self, from_table, from_field, to_table, to_field):
         # print "-- %s.%s -> %s.%s" % (from_table, from_field, to_table, to_field)
         ln = "%s_fk_%s_%s" % (from_field, to_table.split('.')[-1], to_field)
         ln = ln.replace(".",  "_")

         if ln in self.foreign_key_names:
             x = 1
             while (ln+'_'+str(x)) in self.foreign_key_names:
                 x += 1

             ln = ln + '_' + str(x)

         self.foreign_key_names.append(ln)

         self.emit('alter table %s add constraint %s foreign key (%s) references %s (%s);' % (
             from_table, ln, from_field, to_table, to_field))
    def stop(self, schema):
        self.emit("commit;")
class DjangoOut(OutputCollector):

    type_lu = {
        'float': 'models.FloatField(%s)',
        'text': 'models.CharField(max_length=4096,%s)',
        'int': 'models.IntegerField(%s)',
        'bool': 'models.BooleanField(%s)',
        'boolean': 'models.BooleanField(%s)',
        'geometry': 'models.GeometryField(%s)',
        'miscdate': 'miscdate()',
        'date': 'models.DateField(%s)',
        'time': 'models.TimeField(%s)',
        'datetime': 'models.DateTimeField(%s)',
    }

    def __init__(self, *args, **kwargs):

        OutputCollector.__init__(self, *args, **kwargs)
        self.db_schema = kwargs.get('db_schema', '')
        self.validator_id = 0
    def _type_map(self, field):

        type_ = None

        if field.primary_key:
            return 'models.AutoField(primary_key=True)'
        elif field.is_many_to_many():
            # this is created during parsing, shouldn't appear in user visible graph
            # note link table is probably not defined yet, so use string to refer to it
            return 'models.ManyToManyField("%s", through="%s")' % (
                self.upcase(field.name),
                self.upcase(field.foreign_key.table.name),
                )
        elif field.type == 'ID':

            if field.foreign_key_external:
                target = field.foreign_key
            else:
                target = field.foreign_key.table.name
        
            if not field.foreign_key_external and target == field.table.name:
                return 'models.ForeignKey(%s, related_name="%s_set", db_column="%s", %%s)' % (
                    '"self"', field.name, field.name)
            else:
                # use "ModelName" rather than ModelName for reference to avoid
                # declaration order issues
                target_ref = '"%s"'%self.upcase(target)
                if field.foreign_key_external:
                    target_ref = target_ref.strip('"')  # refer to class, not its name
                return 'models.ForeignKey(%s, db_column="%s", %%s)' % (
                    target_ref, field.name)

        elif field.type in self.type_lu:
            ans = self.type_lu[field.type]
            if field.type in ('bool', 'boolean') and field.allow_null:
                # FIXME conflation of null and blank sensu Django here?
                ans = ans.replace("BooleanField", "NullBooleanField")
            return ans
        else:
            return field.type
    def upcase(self, s):

        return s[0].upper() + s[1:]
    def start(self, schema):
        self.emit("# AUTOMATICALLY GENERATED MODELS, edit models_base.py instead\n")
        self.emit("from models_base import *\n")
        self.emit("from django.forms import ValidationError\n")
        self.emit("from django.db.models import Min,Max,Avg,Count\n")
        self.emit('# admin registrations\n"""')
        for table in schema['_tables']:
            self.emit("admin.site.register(%s)" % table.capitalize())
        self.emit('"""\n')

        self.emit("""def dml_dj_set_attr(table, field, attr):
            for fld in table._meta.fields:
                if fld.name == field:
                    fld.dml_attr = attr
                    break
            else:
                raise Exception("Could not find field %s in %s"%(field,table))
        """)
        self.emit("""def dml_dj_add_field_validator(table, field, validator):
            for fld in table._meta.fields:
                if fld.name == field:
                    fld.validators.append(validator)
                    break
            else:
                raise Exception("Could not find field %s"%field)
        """)
    def start_table(self, table):
        
        if not table.comment:
            comment = 'NO COMMENT SUPPLIED'
        else:
            comment = table.comment
            table.attr['dj_description'] = comment

        wrapper = textwrap.TextWrapper(initial_indent='    """',
            subsequent_indent="    ")

        self.emit("class %s (models.Model):  # %s" % (self.upcase(table.name), "AUTOMATICALLY GENERATED"))
        self.emit('%s\n    """' % wrapper.fill(comment))

        # start Meta class
        self.emit()
        self.emit('    class Meta:')
        self.emit('        pass')
        
        if self.db_schema is not None:
            self.emit('        db_table = "%s%s"' % (self.db_schema, table.name))
        
        if table.attr.get('dj_order'):
            self.emit('        ordering = %s' % repr(table.attr.get('dj_order').split()))
        self.emit()
        
        
        # end of Meta class

        # __unicode__
        if table.attr.get('dj_name'):
            self.emit('    def __unicode__(self):')
            self.emit('\n'.join(["        %s %s"%('return' if not n else '      ', i)
                for n,i in enumerate(table.attr.get('dj_name').split('\n'))]))
                
        self.emit()
    def end_table(self, table):
        
        # must come before attribute writing as may update attributes
        self.write_validators(table)

        self.emit()
        
        # DJ complains if attr is present in Meta class def.
        # also, DJ templates can't access attributes starting with '_'
        self.emit()
        self.emit('%s.dml_attr = %s'%(self.upcase(table.name), repr(table.attr)))
        
        self.emit()

        # write DML attributes on fields as well
        for fld in table.field:
            F = table.field[fld]
            self.emit('dml_dj_set_attr(%s, "%s", %s)'%(
                self.upcase(table.name),
                F.name,
                repr(F.attr)))
        
        self.emit()
    def show_field(self, field):

        plural = 's' if field.is_many_to_many() else ''
        
        field.attr['dj_description'] = field.comment

        fld = "    %s%s = %s" % (
            field.name,
            plural,
            self._type_map(field),
        )

        if '%s' in fld:  # don't mess with pk fields etc.

            kwargs = []
            if field.unique:
                kwargs.append('unique=True')
            if field.allow_null:
                kwargs.append('blank=True')
                if ('text' not in field.type.lower() and
                    'char' not in field.type.lower()):
                         kwargs.append('null=True')
            if not field.editable or field.attr.get('dj_editable') == 'false':
                kwargs.append('editable=False')
                
            if field.attr.get('choices'):                   
                kwargs.append('choices=(%s)'%field.attr.get('choices'))

            fld = fld % (', '.join(kwargs))

        self.emit(fld)

        if field.comment:
            wrapper = textwrap.TextWrapper(initial_indent='    # ',
                subsequent_indent='    # ')
            self.emit(wrapper.fill(field.comment))
    def show_link(self, from_table, from_field, to_table, to_field):
         self.emit("# %s.%s -> %s.%s" % (from_table, from_field, to_table, to_field))
    def stop(self, schema):
        pass
    def write_validators(self, table, field=None):

        if field:
            validators = field.validators
        else:
            validators = table.validators
            
        for validator in validators:

            v_name = 'validate_%s' % table.name
            if field:
                v_name += '_%s' % field.name
                
            v_name += '_%s' % self.validator_id
            self.validator_id += 1
            
            self.emit("def %s(X, pk=None):" % v_name)
            self.emit('\n'.join(["    "+i for i in validator['rule'].split('\n')]))
            self.emit("    if not ok:")
            self.emit("        raise ValidationError(%s)" % repr(validator['message']))
            self.emit("")
            
            if field:
                self.emit("dml_dj_add_field_validator(%s, %s, %s)" % (
                    self.upcase(table.name), repr(field.name), v_name))
            else:
                table.attr.setdefault('dml_validators', []).append(v_name)
                    
        if not field:
            for field_name in table.field:
                self.write_validators(table, field=table.field[field_name])

FIRST_CONNECT = 12

NS = { 'dia': "http://www.lysator.liu.se/~alla/dia/" }

def read_dia(doc, schema):
    
    tables = doc.xpath('//dia:object[@type="Database - Table"]', namespaces=NS)
    
    for table in tables:
    
        T = Table()
    
        for i in 'name', 'comment':
            setattr(T, i, table.xpath('./dia:attribute[@name="%s"]/dia:string'%i,
                namespaces=NS)[0].text.strip('#'))
    
        #X T.name = T.name ???
    
        schema['o2t'][table.get('id')] = T.name
        schema['_tables'].append(T.name)  # for ordering
        schema[T.name] = T
    
        connection = FIRST_CONNECT
    
        fields = table.xpath('.//*[@type="table_attribute"]')
        for field in fields:
            F = Field(T)
    
            # attribs always present even if empty, so
            for i in 'name', 'type', 'comment':
                val = field.xpath('./dia:attribute[@name="%s"]/dia:string'%i,
                    namespaces=NS)[0].text.strip('#')
                setattr(F, i, val)
                if i == 'comment' and val.strip() == "" and F.type != 'ID':
                    sys.stderr.write("WARNING: %s.%s has no %s\n" %
                        (T.name, F.name, i))
                    
            for tag_char in '-*-':  # FIXME stupid code, - repeated to cover ordering
                if F.name[0] == tag_char or F.name[-1] == tag_char:
                    F.name = F.name.strip(tag_char)
                    if tag_char == "*":
                        if 'dj_order' in T.attr:
                            T.attr['dj_order'] += ' '
                        else:
                            T.attr['dj_order'] = ''
                        T.attr['dj_order'] += F.name
                    if tag_char == "-":
                        F.editable = False
                        
            for i in 'primary_key', 'nullable', 'unique':
                is_i = field.xpath(
                    './dia:attribute[@name="%s"]/dia:boolean/@val'%i,
                    namespaces=NS)[0]
                setattr(F, i, is_i == 'true')
                
            F.allow_null = F.nullable
                
            T.fields.append(F.name)  # for ordering
            T.field[F.name] = F
    
            T.c2f[str(connection)] = F.name
            connection += 1
            T.c2f[str(connection)] = F.name
            connection += 1
    
    connections = doc.xpath('//dia:object[@type="Database - Reference"]', namespaces=NS)
    
    for connection in connections:
    
        connects = connection.xpath('.//dia:connection', namespaces=NS)
        if len(connects) != 2:
            sys.stderr.write('Bad connector, does not have 2 connections\n');
            raise SystemExit
    
        from_table = schema[schema['o2t'][connects[0].get('to')]]
        from_field = from_table.field[from_table.c2f[connects[0].get('connection')]]
        to_table = schema[schema['o2t'][connects[1].get('to')]]
        to_field = to_table.field[to_table.c2f[connects[1].get('connection')]]
    
        from_field.foreign_key = to_field
        to_field.referers.append(from_field)
    
        # out.show_link(from_table.name, from_field.name, to_table.name, to_field.name)



def any_to_bool(s):
    
    if not s:  # 0 and None and "" and []
        return False
        
    s = str(s).strip().lower()
    
    if not s:  # "  "
        return False
    
    if s[0] in 'n0f':  # 'false', 'No', '0', '0.1', 'Foo'
        return False
        
    return True

def read_dml(doc, schema):
    
    dml = doc.getroot()
    
    for i in 'name', 'description':
        xp = dml.xpath(i)
        if xp:
            schema['_'+i] = xp[0].text
        else:
            schema['_'+i] = ''
            
    schema['_attr'] = {}
    for i in dml.xpath('attr'):
        schema['_attr'][i.get('key')] = i.text
        
    schema['_log'] = []
    for i in dml.xpath('log/log_entry'):
        schema['_log'].append((i.get('date'), i.text))
    
    tables = doc.xpath('//table')
    
    for table in tables:  # pass 1 - create fields
    
        T = Table()
        
        T.name = table.xpath('name')[0].text
            
        T.comment = '\n'.join([i.text or '' for i in table.xpath('./description')])
        
        T.attr = {}
        for i in table.xpath('attr'):
            T.attr[i.get('key')] = i.text

        for i in table.xpath('validator'):
            T.validators.append({
                'rule': i.xpath('rule')[0].text,
                'message': i.xpath('message')[0].text,
            })


        #X schema['o2t'][table.get('id')] = T.name
        
        schema['_tables'].append(T.name)  # for ordering
        schema[T.name] = T

        fields = table.xpath('.//field')
        for field in fields:
            F = Field(T)

            F.attr = {}
            for i in field.xpath('attr'):
                F.attr[i.get('key')] = i.text
                
            for i in field.xpath('validator'):
                F.validators.append({
                    'rule': i.xpath('rule')[0].text,
                    'message': i.xpath('message')[0].text,
                })

            for i in ['primary_key', 'allow_null', 'unique']:
                setattr(F, i, any_to_bool(field.get(i)))

            # attribs always present even if empty, so
            F.name = field.xpath('name')[0].text
            F.type = field.xpath('type')[0].text
                
            F.comment = '\n'.join([i.text or '' for i in field.xpath('./description')])
             
            T.fields.append(F.name)  # for ordering
            T.field[F.name] = F
    
    for table in tables:  # pass 2 - add links
    
        fields = table.xpath('.//field')
        for field in fields:
            
            for fk in field.xpath('.//foreign_key'):
                
                target = doc.xpath("//field[@id='%s']"%fk.get('target'))

                from_table = schema[table.xpath('name')[0].text]
                from_field = from_table.field[field.xpath('name')[0].text]
                
                if target:                    
                    target = target[0]
                    to_table = schema[target.getparent().xpath('name')[0].text]
                    to_field = to_table.field[target.xpath('name')[0].text]
                    from_field.foreign_key = to_field
                    to_field.referers.append(from_field)
                    from_field.foreign_key_external = False
                else:  # assume external defintion
                    from_field.foreign_key = fk.get('target')
                    from_field.foreign_key_external = True
def read_dml_old(doc, schema):
    
    if doc.getroot().get('db_schema'):
        schema['_db_schema'] = doc.getroot().get('db_schema')
    
    tables = doc.xpath('//table')
    
    for table in tables:  # pass 1 - create fields
    
        T = Table()
        
        for i in ['name']:
            setattr(T, i, table.get(i))
            
        T.comment = '\n'.join([i.text or '' for i in table.xpath('./description')])

        #X schema['o2t'][table.get('id')] = T.name
        
        schema['_tables'].append(T.name)  # for ordering
        schema[T.name] = T

        fields = table.xpath('.//field')
        for field in fields:
            F = Field(T)
    
            for i in ['primary_key', 'nullable', 'unique', 'editable']:
                setattr(F, i, any_to_bool(field.get(i)))

            # attribs always present even if empty, so
            for i in 'name', 'type':
                val = field.get(i)
                setattr(F, i, val)
                
            F.comment = '\n'.join([i.text or '' for i in field.xpath('./description')])
             
            T.fields.append(F.name)  # for ordering
            T.field[F.name] = F
    
    for table in tables:  # pass 2 - add links
    
        fields = table.xpath('.//field')
        for field in fields:
            
            for fk in field.xpath('.//foreign_key'):
                
                target = doc.xpath("//field[@id='%s']"%fk.get('target'))[0]

                from_table = schema[table.get('name')]
                from_field = from_table.field[field.get('name')]
                to_table = schema[target.getparent().get('name')]
                to_field = to_table.field[target.get('name')]
            
                from_field.foreign_key = to_field
                to_field.referers.append(from_field)


def read_schema(doc):
    
    schema = {
        'o2t':{},      # table id to name, used by read_dia
        '_tables':[],  # for ordering
    }

    tables = doc.xpath('//dia:object[@type="Database - Table"]', namespaces=NS)
    
    if tables:
        read_dia(doc, schema)
    else:
        read_dml(doc, schema)
    
    # now futz with table ordering so foreign_key references are available
    # first find dependencies for each table
    for table in schema['_tables']:
    
        T = schema[table]
    
        T.depends = set()
    
        for field in T.fields:
            F = T.field[field]
            if F.foreign_key and not F.foreign_key_external:
                T.depends.add(F.foreign_key.table.name)
    
        #D sys.stderr.write('%s: %s\n'%(T.name, T.depends))
    
    # then sort accordingly (tried the sort using 
    # http://code.activestate.com/recipes/576653/ to get sort (cmp) back,
    # but that doesn't work, so bubble sort style)
    #D sys.stderr.write('%s\n'%str(schema['_tables']))
    start_idx = 0
    
    while start_idx < len(schema['_tables']):
        T = schema[schema['_tables'][start_idx]]
        for idx in range(len(schema['_tables'])-1, start_idx-1, -1):
            # start from end to get max required move
            if (schema['_tables'][idx] in T.depends
                and not schema['_tables'][idx] == T.name):  
                # beware self-dependent tables
                # swap
                schema['_tables'][start_idx],schema['_tables'][idx] = (
                    schema['_tables'][idx],schema['_tables'][start_idx])
                break
        else:
            start_idx += 1
    #D sys.stderr.write('%s\n'%str(schema['_tables']))
    
    # add many to many references
    for table in schema['_tables']:
    
        T = schema[table]
        if T.is_many_to_many():
            for f in T.fields[1:]:
                for t in T.fields[1:]:
    
                    if t == f or T.field[f].type != 'ID' or T.field[t].type != 'ID':
                        continue  # link carries additional info.
    
                    schema[f].fields.append(t)
                    F = Field(schema[f])
                    F.m2m_link = True
                    F.name = t
                    schema[f].field[t] = F
                    F.type = 'ID'
                    F.foreign_key = T.field[f]
                    
    return schema

def main():
    parser = optparse.OptionParser()
    parser.add_option("--mode", default="django",
        help="Output mode: django (default), SQL, simple")
    
    opt, arg = parser.parse_args()
    mode = {
        'django': DjangoOut,
        'SQL': SQLOut,
        'simple': SimpleOut,
        'rst': RstOut,
        'dml': DMLOut,
    }
    
    
    doc = etree.parse(arg[0])
    
    schema = read_schema(doc)
    
    import pprint
    sys.stderr.write(pprint.pformat(schema)+'\n')
    
    out = mode[opt.mode](schema)
    out.start(schema)
    
    # main output pass
    for table in schema['_tables']:
    
        T = schema[table]
    
        out.start_table(T)
    
        for field in T.fields:
            F = T.field[field]
            
            try:
                out.show_field(F)
            except Exception:
                sys.stderr.write("Error writing %s.%s\n" % (table, field))
                raise
    
        out.end_table(T)
    
    # pass for SQL output which uses "alter table" to add links
    for table in schema['_tables']:
    
        T = schema[table]
    
        for field in T.fields:
            F = T.field[field]
            if F.foreign_key and not F.foreign_key_external:
                out.show_link(T.name, F.name,
                    F.foreign_key.table.name, F.foreign_key.name)
                    
    out.stop(schema)
    
    print out.result()


if __name__ == '__main__':
    main()