# AxonDb demo

```bash
export AXON_DB_PATH=/tmp/axondb-demo.db
python -m axon.cli add --text 'The deployment window is Thursday at 10:00' --tag ops
python -m axon.cli add --text 'Maya owns the weekly product metrics report' --tag product
python -m axon.cli recall 'Who owns the metrics report?'
```
