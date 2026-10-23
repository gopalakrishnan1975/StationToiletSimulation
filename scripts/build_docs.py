"""Run design tests, then generate reference results and executable contract documentation."""
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    out=ROOT/'docs/generated';out.mkdir(parents=True,exist_ok=True)
    artifacts=ROOT/'artifacts';artifacts.mkdir(exist_ok=True)
    result=subprocess.run([sys.executable,'-m','pytest','-q','tests','--junitxml='+str(artifacts/'tests.xml')],cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
    from api import app as calculation
    from data_api import app as data
    from services.data import TrainCall
    from services.experiments import compare_layouts
    from services.infrastructure import Inputs,calculate
    from services.welfare import compare
    from services.funding import Funding,evaluate
    for name,obj in [('calculation_openapi.json',calculation.openapi()),('data_openapi.json',data.openapi()),('train_call_schema.json',TrainCall.model_json_schema())]:
        (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    baseline={'version':'6.0.0','infrastructure':calculate(Inputs()),'welfare':compare(Inputs()),
              'funding':evaluate(Funding(),Inputs()),
              'layouts':compare_layouts(1000,.25,600,30,30,3,20,(9,6,18,3),3)}
    (out/'reference_outputs.json').write_text(json.dumps(baseline,indent=2,sort_keys=True)+'\n')
    tests=ET.parse(artifacts/'tests.xml').getroot().findall('.//testcase')
    # Deterministic content fingerprint: excludes generated files, runtime data and secrets.
    paths=sorted([*ROOT.glob('*.py'),*ROOT.glob('services/*.py'),*ROOT.glob('tests/*.py'),*ROOT.glob('scripts/*.py'),ROOT/'requirements.txt',ROOT/'requirements-dev.txt'])
    digest=hashlib.sha256(b''.join(str(p.relative_to(ROOT)).encode()+b'\0'+p.read_bytes() for p in paths)).hexdigest()
    lines=['# Generated validation report','','Version 6.0.0',f'Validated source fingerprint: `{digest}`','',f'**{len(tests)} tests passed.** Generated only after successful tests; regenerate whenever source changes.','','| Test | Result |','|---|---|']
    lines += [f'| `{t.attrib["name"]}` | Passed |' for t in tests]
    lines += ['','## Validation scope','','Unit and deterministic queue invariants, synthetic CSV validation, SQLite integration, HTTP authentication and calculation contracts, Streamlit render, observed-data run and stale-result protection.','','No live PostgreSQL server, CRIS entitlement, real station data, field calibration, load test or production security review was exercised. The hosted Streamlit smoke test is performed separately after deployment.','','## Reference scenario','','20 trains/day; 1,000 boardings/train; 25% potential use; 37.5% urinal share; three blocks with 36 total fixtures. Peak comparison: 3 trains, 20 replications. Engineering uses potential daily demand.','','| Layout | Completed/train | Unmet/train | Overall target |','|---|---:|---:|---|']
    lines += [f'| {r["Layout"]} | {r["Completed visits / train"]} | {r["Unmet attempts / train"]} | {r["Overall service target"]} |' for r in baseline['layouts']]
    lines += ['','All values are synthetic planning outputs. See TECHNICAL_GUIDE.md and DESIGN_AUDIT.md for assumptions and limitations.','']
    (out/'VALIDATION_REPORT.md').write_text('\n'.join(lines))
    print(f'Generated documentation for {len(tests)} passing tests')

if __name__=='__main__':main()
