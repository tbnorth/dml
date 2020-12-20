set -e
SOURCE=fish.g2.dml
cp "$SOURCE" workdir/orig.dml
python ../dmlio.py --mode dml workdir/orig.dml >workdir/identity.dml
python ../dmlio.py --mode yaml workdir/orig.dml >workdir/yaml.yaml
python ../dmlio.py --mode json workdir/orig.dml >workdir/json.json
python ../dmlio.py --mode dml workdir/yaml.yaml >workdir/yaml.dml
python ../dmlio.py --mode dml workdir/json.json >workdir/json.dml
python ../dotgraph.py workdir/orig.dml workdir/orig.pdf
python ../dotgraph.py workdir/identity.dml workdir/identity.pdf
python ../dotgraph.py workdir/yaml.dml workdir/yaml.pdf
python ../dotgraph.py workdir/json.dml workdir/json.pdf
echo evince workdir/orig.pdf workdir/identity.pdf \
            workdir/yaml.pdf workdir/json.pdf





