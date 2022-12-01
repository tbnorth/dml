# DML - Database Markup Language

## History

This is a very old tool, probably years older than its git history. It was
originally designed to generate SQL from [Dia
diagrams](https://en.wikipedia.org/wiki/Dia_(software)).  It is intended as a
very simple, RDMS agnostic schema representation, with an emphasis on
generating outputs in multiple complimentary forms (SQL,
[Django](https://www.djangoproject.com/) model classes,
[graphviz](https://graphviz.org/) diagrams).  It did a lot of work with the [Leo editor](https://leoeditor.com/) being used as
a domain aware XML editing environment.

## Formats

| Format       | Read | Write | Status                   |
| ---          | ---  | ---   | ---                      |
| DIA          | Y    | N     | Broken, deprecated       |
| Django model | N    | Y     | Needs update to Django 3 |
| JSON         | Y    | Y     | Good                     |
| Leo          | Y    | Y     | Broken, deprecated       |
| MDB          | Y    | N     | ???                      |
| PDF          | N    | Y     | Write via dot            |
| PNG          | N    | Y     | Write via dot            |
| SQL          | ?    | Y     | Good                     |
| SVG          | N    | Y     | Write via dot            |
| XML          | Y    | Y     | Good                     |
| YAML         | Y    | Y     | Good                     |
| dot          | N    | Y     | Good                     |

## Current (2020-11) status

Needs major cleanup and tests, "Good" in the table above indicates intent, not
that it's currently working.

Need to resolve issue with XML:

```xml
<table>
  <name>addresses</name>
  <name context="long">client contact addresses</name>
```

not translating easily into YAML / JSON etc.,

```yaml
table:
  name:
    context: this is clumsy
    value: addresses
```

Probably just drop from supported representation.

