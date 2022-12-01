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
| Django model | N    | Y     | Working, Django 4 only   |
| JSON         | Y    | Y     | Good                     |
| Leo          | Y    | Y     | Broken, deprecated       |
| MDB          | Y    | N     | ???                      |
| PDF          | N    | Y     | Write via dot            |
| PNG          | N    | Y     | Write via dot            |
| SQL          | ?    | Y     | Untested                 |
| SVG          | N    | Y     | Write via dot            |
| XML          | Y    | Y     | Working                  |
| YAML         | Y    | Y     | Working                  |
| dot          | N    | Y     | Working                  |

## Current (2022) status

Round tripping XML / JSON / YAML, writes usable Django 4 models.

### Old note
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

