from pathlib import Path
import os,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
sys.dont_write_bytecode=True
os.chdir(ROOT/'backend')
from app.models import appeal_guidance_service as g, appeal_rewrite_validator as rv, appeal_generation_service as ag
cases=json.loads((ROOT/'investigation_output/cases.json').read_text(encoding='utf-8'))
t=cases[0]['text']
variants={
'original':t,
'paragraphs_only':t.replace('. ','.\n\n'),
'split_long_sentence':t.replace('Academic talent is everywhere, but equal opportunity is not, leaving thousands of capable young minds locked out of the future they have worked so hard to build.', 'Academic talent is everywhere, but equal opportunity is not. Thousands of capable young minds are locked out of the future they have worked so hard to build.'),
'remove_filler':t.replace('Brilliant students','Students').replace('simply because','because').replace('Your gift to our scholarship fund breaks down these financial barriers, directly providing','Your gift to our scholarship fund provides').replace('By investing in their education today, you are not just funding a degree—you are empowering the next generation of innovators, leaders, and problem-solvers to change our world.','Please support these students.'),
'append_grounded_request':t+' Please support these students.',
'facts_only_shorter': 'Students from low-income families cannot afford the cost of tuition and textbooks. Your gift to our scholarship fund provides tuition assistance, mentorship, and resources students need to stay in school and graduate. Please support these students.'
}
a=g.quality._load_artifacts()
print('FACT_PRESERVING_WORDING_PROBES (model response; guard validation reported separately)')
for (name,text),score in zip(variants.items(),g.batch_score(list(variants.values()))):
    print('\nVARIANT',name)
    print('TEXT_BEGIN\n'+text+'\nTEXT_END')
    print('SCORE',json.dumps(score))
    print('GUARD',rv.validate_rewrite(t,text),'actual_gate',rv.is_safe_rewrite(t,text,fallback=ag._safe_rewrite))
    print('HAND',dict(zip(a['cfg']['scaler_feature_names'],g.quality._handcrafted(text,'English',a)[0].tolist())))
data=(ROOT/'dataset/Donation_Appeal_MASTER_FINAL_v8_7100.csv').read_bytes()
print('DATASET_RAW_SHA256',hashlib.sha256(data).hexdigest())
print('DATASET_LF_SHA256',hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest())
print('DATASET_CRLF_SHA256',hashlib.sha256(data.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest())
