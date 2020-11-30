import sys
from lxml import etree
import subprocess
import os
import tempfile

log = sys.stderr.write


def dotgraph(xml_, output=None, links_only=False, title=""):

    dot = makedot(xml_, links_only=links_only, title=title)
    if output:
        with open(output + '.dot', 'w') as out:
            out.write(dot)

    cmd = subprocess.Popen(
        ['dot', '-Tpdf'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        env=os.environ.copy(),
    )
    png, _ = cmd.communicate(dot.encode('utf-8'))

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


def get_name(ele):
    names = ele.xpath('name')
    if names:
        name = names[0].text
    else:
        name = ele.get('name')
    return name.strip()


def makedot(xml_, links_only=False, title="dd"):

    dom = etree.fromstring(xml_.encode('utf-8'))
    dot = [
        '\ndigraph tables {',
        'graph [rankdir = RL, label="%s", labelloc=t];' % title,
        'node [shape = plaintext];',
        'subgraph cluster_key { label=Key;',
        '_tn [width=1.8, label = "TABLE NAME", filled=True, shape=box, '
        'style=filled, fillcolor="#ccccff", rank=max];',
        '_pk [width=1.8, label = "PRIMARY KEY", shape=box, '
        'fontcolor="red", rank=max];',
        '_un [width=1.8, label = "UNIQUE", filled=True, shape=box, '
        'style=filled, fillcolor="#ccffcc", rank=min];',
        '_op [width=1.8, label = "OPTIONAL", shape=box, '
        'fontcolor="#888888", rank=max];',
        '}',
    ]

    lu = {}

    # find fields pointed to by Foreign Key fields, don't assume FKs only
    # point to Primary Keys
    fk_targets = dom.xpath('//field/foreign_key/@target')

    for table in dom.xpath('//table'):

        skip = table.xpath('./attr[@key="dot_ignore"]')
        if skip and skip[0].text == 'true':
            continue

        name = get_name(table) + ' [label='

        ports = [
            '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR>'
            '<TD BGCOLOR="#ccccff">%s</TD></TR>' % get_name(table)
        ]
        for field in table.xpath('./field'):

            if (
                links_only
                and not field.get('primary_key') == 'true'
                and not field.get('id') in fk_targets
                and not field.xpath('.//foreign_key')
            ):
                continue

            lu[field.get('id')] = "%s:%s" % (
                get_name(table),
                field.get('id'),
            )

            fname = get_name(field)
            if field.get('allow_null') == 'true':
                fname = '<FONT COLOR="#888888">%s</FONT>' % fname
            if field.get('primary_key') == 'true':
                fname = '<FONT COLOR="red">%s</FONT>' % fname

            attr = ''
            if (
                field.get('unique') == 'true'
                or field.get('primary_key') == 'true'
            ):
                attr = ' BGCOLOR="#ccffcc"'

            ports.append(
                '<TR><TD PORT="%s"%s>%s</TD></TR>'
                % (field.get('id'), attr, fname)
            )

        name += '\n'.join(ports)

        name += '</TABLE>>];'

        dot.append(name)

    for table in dom.xpath('//table'):

        skip = table.xpath('./attr[@key="dot_ignore"]')
        if skip and skip[0].text == 'true':
            continue

        name = get_name(table)
        for field in table.xpath('./field'):
            for fk in field.xpath('./foreign_key'):
                if fk.get('target') in lu:
                    dot.append(
                        '%s:%s -> %s'
                        % (name, field.get('id'), lu[fk.get('target')])
                    )
                else:
                    log(
                        "No '%s' target for %s:%s\n"
                        % (fk.get('target'), name, field.get('id'))
                    )

        for m2m in table.xpath('./attr'):
            if m2m.get('key') != 'dj_m2m_target':
                continue
            # break
            for line in m2m.text.strip().split('\n'):
                # dot.append('%s -> %s [label="%s"]' %
                # (name, line.split()[1], line.split()[0]))
                dot.append('%s -> %s' % (name, line.split()[1]))

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
