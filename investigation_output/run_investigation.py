from pathlib import Path
import ast, sys, os, json, asyncio, logging, hashlib, re
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation_output'
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
os.chdir(ROOT / 'backend')
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s')
paths = ['backend/app/models/main.py', 'backend/app/models/appeal_generation_service.py', 'backend/app/models/appeal_rewrite_validator.py', 'backend/app/models/appeal_guidance_service.py', 'backend/app/models/quality_service.py', 'backend/app/models/gemini_service.py', 'backend/app/models/appeal_improvement_selection.py', 'backend/app/services/appeal_budget.py', 'frontend/src/pages/DonationAppealAnalyzer.jsx', 'frontend/src/config/appealLengths.json']
baseline = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
with (OUT/'source.txt').open('w', encoding='utf-8', newline='') as f:
    for p in paths:
        f.write('\n===== '+p+' =====\n')
        f.write((ROOT/p).read_bytes().decode('utf-8'))
from app.models import appeal_generation_service as ag, appeal_rewrite_validator as rv, appeal_guidance_service as guide, gemini_service as gs
from app.models.config import settings
# Temporary in-memory instrumentation adds only print statements to application functions.
source = (ROOT/'backend/app/models/appeal_generation_service.py').read_text(encoding='utf-8')
source = source.replace('            facts_ok = is_safe_rewrite(text, rewrite, fallback=_safe_rewrite)', '            print("RAW_GEMINI_OUTPUT_BEGIN", flush=True)\n            print(rewrite, flush=True)\n            print("RAW_GEMINI_OUTPUT_END", flush=True)\n            facts_ok = is_safe_rewrite(text, rewrite, fallback=_safe_rewrite)')
exec(compile(source, ag.__file__, 'exec'), ag.__dict__)
provider_source = (ROOT/'backend/app/models/gemini_service.py').read_text(encoding='utf-8')
provider_tree = ast.parse(provider_source)
node = next(n for n in provider_tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'call_gemini_with_key')
provider_fn = ast.get_source_segment(provider_source, node)
provider_fn = provider_fn.replace('        with requests.Session() as session:', '        print("EXACT_REQUEST_BODY_BEGIN", flush=True)\n        print(__import__("json").dumps(body, ensure_ascii=False, indent=2), flush=True)\n        print("EXACT_REQUEST_BODY_END", flush=True)\n        with requests.Session() as session:')
exec(compile(provider_fn, gs.__file__, 'exec'), gs.__dict__)
# Load only the corpus/group functions and their literal constants. Never execute training.
import numpy as np, pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold
train = ast.parse((ROOT/'backend/ml_models/Donation Appeal/training/train_quality_v3.py').read_text(encoding='utf-8'))
selected = [n for n in train.body if (isinstance(n, ast.FunctionDef) and n.name in ('load_corpus','build_groups')) or (isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('LANGUAGES','LABELS','LANG_SPEC','NEAR_DUPLICATE_THRESHOLD') for t in n.targets))]
ns = dict(np=np, pd=pd, coo_matrix=coo_matrix, connected_components=connected_components, TfidfVectorizer=TfidfVectorizer)
exec(compile(ast.Module(body=selected, type_ignores=[]), '<original split helpers>', 'exec'), ns)
data_path=ROOT/'dataset/Donation_Appeal_MASTER_FINAL_v8_7100.csv'
df, info = ns['load_corpus'](data_path)
groups = ns['build_groups'](df)
_, test_idx = next(iter(StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42).split(np.zeros(len(df)),(df.language+'_'+df.quality_label).values,groups)))
test=df.iloc[test_idx]
manifest=json.loads(settings.donation_appeal_model_path('manifest.json').read_text())
print('DATASET_SHA256',hashlib.sha256(data_path.read_bytes()).hexdigest(),'MANIFEST_SHA256',manifest['data_sha256'],flush=True)
assert len(test)==manifest['test_rows']
predictions=pd.read_csv(settings.donation_appeal_model_path('test_predictions.csv'))
assert predictions.language.tolist()==test.language.tolist()
assert predictions.true_label.tolist()==test.quality_label.tolist()
assert np.allclose(predictions.true_score.values,test.overall_quality_score.values)
print('TEST_SPLIT_VERIFIED',json.dumps(info), 'test_rows',len(test),flush=True)
appeal='Brilliant students from low-income families are being forced to abandon their dreams of a college education simply because they cannot afford the cost of tuition and textbooks. Academic talent is everywhere, but equal opportunity is not, leaving thousands of capable young minds locked out of the future they have worked so hard to build. Your gift to our scholarship fund breaks down these financial barriers, directly providing the tuition assistance, mentorship, and resources hard-working students need to stay in school and graduate. By investing in their education today, you are not just funding a degree—you are empowering the next generation of innovators, leaders, and problem-solvers to change our world.'
cases=[dict(id='user_scholarship', text=appeal, label='user-provided')]
for label, count in [('low',2),('medium',2),('high',1)]:
    for index,row in test[(test.language=='English') & (test.quality_label==label)].head(count).iterrows():
        cases.append(dict(id='test_row_'+str(index),text=row.appeal_text,label=label))
(OUT/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
a=guide.quality._load_artifacts()
print('RUNTIME',sys.version,flush=True)
print('MODEL_DIR',settings.donation_appeal_model_path(''),flush=True)
print('MODEL_CONFIG',repr(a['cfg']),flush=True)
print('TFIDF_PARAMS',repr(a['tfidf_en'].get_params()),flush=True)
print('FEATURE_DIMENSIONS',json.dumps({'hand':len(a['cfg']['scaler_feature_names']),'tf_en':a['N_EN'],'tf_si':a['N_SI'],'tf_ta':a['N_TA'],'lsa':a['cfg']['lsa_components']}),flush=True)
print('MODEL_TYPES',repr({k:type(a[k]).__name__ for k in ('clf','reg','iso')}),flush=True)
rows=[]
async def run():
    for case in cases:
        print('\nCASE_BEGIN',case['id'],'test_label',case['label'],flush=True)
        print('ORIGINAL_BEGIN\n'+case['text']+'\nORIGINAL_END',flush=True)
        captures=[]
        def trace(frame,event,arg):
            if event=='return' and frame.f_code.co_name=='is_safe_rewrite' and frame.f_globals.get('__name__')==rv.__name__:
                captures.append(dict(frame.f_locals))
            return trace
        sys.settrace(trace)
        try:
            result=await ag.repair(case['text'],{'language':'English'},client='investigation_20261017')
        finally:
            sys.settrace(None)
        print('FLOW_RESULT',json.dumps(result,ensure_ascii=False),flush=True)
        record=dict(id=case['id'],test_label=case['label'],original_score=result['original_score'],original_raw_score=result['original_raw_quality_score'],raw_gemini_score=None,guard_passed=None,guard_reason=None,flow_rejection=result['rejection_reason'])
        print('ORIGINAL_HAND_FEATURES',repr(dict(zip(a['cfg']['scaler_feature_names'],guide.quality._handcrafted(case['text'],'English',a)[0].tolist()))),flush=True)
        if captures:
            raw=captures[-1]['rewrite']
            validation=captures[-1]['result']
            record.update(raw_gemini_score=guide.batch_score([raw],'English')[0],guard_passed=captures[-1].get('result').accepted,guard_reason=validation.reason,raw_output=raw)
            print('RAW_GEMINI_MODEL_SCORE',json.dumps(record['raw_gemini_score']),flush=True)
            print('GUARD_VALIDATION',repr(validation),'ACTUAL_GATE',result.get('rejection_reason'),flush=True)
            print('LENGTH_GUARD',repr(guide.length_warning(raw,'short')),flush=True)
            if validation.reason=='unsupported_language':
                print('FALLBACK_GATE_RESULT',ag._safe_rewrite(case['text'],raw),flush=True)
                record['guard_passed']=ag._safe_rewrite(case['text'],raw)
            # Trace the original validator, printing the precise failing clause and rule locals.
            def diag(frame,event,arg):
                if event=='return' and frame.f_code.co_name=='validate_rewrite':
                    loc=frame.f_locals
                    print('GUARD_EXACT_RETURN',repr(arg),flush=True)
                    if 'sentence' in loc:
                        print('GUARD_FAILING_CLAUSE',repr(loc['sentence']),flush=True)
                        print('GUARD_CLAUSE_TOKENS',repr(loc.get('content')),flush=True)
                        print('GUARD_SCOPE',repr(set(loc.get('content',[])) & rv._SCOPE),'past',loc.get('past'),'inherited',repr(loc.get('context')),flush=True)
                        orig_forms=set().union(*(rv._forms(w) for w in rv._tokens(rv._normalise(case['text']))))
                        print('GUARD_NEW_CONTENT_TOKENS',repr([w for w in loc.get('content',[]) if not (rv._forms(w)&orig_forms)]),flush=True)
                        for src,past,ctx in loc.get('sentences',[]):
                            if rv._subsequence(loc.get('content',[]),src):
                                print('GUARD_ORDER_MATCH_BUT_SCOPE_OR_TENSE_MISMATCH',repr({'source':src,'past':past,'scope':set(src)&rv._SCOPE,'inherited':ctx}),flush=True)
                return diag
            sys.settrace(diag)
            try: rv.validate_rewrite(case['text'],raw)
            finally: sys.settrace(None)
        rows.append(record)
        (OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        print('CASE_END',case['id'],flush=True)
asyncio.run(run())
print('\nTABLE_BEGIN\nid | test label | original score | Gemini output score | guard passed? | guard reason | flow rejection',flush=True)
for row in rows:
    print(' | '.join(str(x) for x in [row['id'],row['test_label'],row['original_score'],row['raw_gemini_score']['quality_score'] if row['raw_gemini_score'] else 'unavailable',row['guard_passed'],row['guard_reason'],row['flow_rejection']]),flush=True)
print('TABLE_END',flush=True)
print('SOURCE_UNCHANGED',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in baseline.items()),flush=True)


