from pathlib import Path
import sys,os,json,re,ast,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend')); sys.dont_write_bytecode=True; os.chdir(ROOT/'backend')
from app.models import appeal_rewrite_validator as rv, appeal_generation_service as ag
cases=json.loads((ROOT/'investigation_output/cases.json').read_text(encoding='utf-8'))
results=json.loads((ROOT/'investigation_output/results.json').read_text(encoding='utf-8'))
for case,row in zip(cases,results):
    print('\nCASE',case['id'])
    original,rewrite=case['text'],row['raw_output']
    locs=[]
    def trace(frame,event,arg):
        if event=='return' and frame.f_code.co_name=='validate_rewrite': locs.append(dict(frame.f_locals))
        return trace
    sys.settrace(trace)
    try: outcome=rv.validate_rewrite(original,rewrite)
    finally: sys.settrace(None)
    print('VALIDATOR',outcome)
    loc=locs[-1]
    if outcome.reason=='unsupported_language':
        print('NON_ASCII_ALPHA',repr(sorted({c for c in rv._normalise(original+rewrite) if c.isalpha() and ord(c)>127})))
        words=lambda text:set(re.findall(r'[^\W\d_]+',text.casefold(),re.UNICODE))
        tree=ast.parse((ROOT/'backend/app/models/appeal_generation_service.py').read_text(encoding='utf-8'))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_safe_rewrite')
        neutral_stmt=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='neutral' for t in n.targets))
        ns={}; exec(compile(ast.Module(body=[neutral_stmt],type_ignores=[]),'<unchanged neutral set>', 'exec'),ns)
        neutral=ns['neutral']-{'today','families','people','affected','community','verified'}
        print('FALLBACK_NEW_DISALLOWED_TOKENS',repr(sorted(words(rewrite)-(words(original)|neutral))))
        print('FALLBACK_RESULT',ag._safe_rewrite(original,rewrite))
    elif outcome.reason=='changed_quantity':
        numbers=lambda text:set(re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:\s*%)?',text))
        print('ORIGINAL_QUANTITIES',repr(sorted(numbers(original))))
        print('REWRITE_QUANTITIES',repr(sorted(numbers(rewrite))))
        print('REMOVED_QUANTITIES',repr(sorted(numbers(original)-numbers(rewrite))))
        print('ADDED_QUANTITIES',repr(sorted(numbers(rewrite)-numbers(original))))
    if 'sentence' in loc:
        print('FIRST_FAILING_CLAUSE',repr(loc['sentence']))
        print('CONTENT_TOKENS',repr(loc['content']))
        print('CLAUSE_SCOPE',repr(set(loc['content'])&rv._SCOPE),'PAST',repr(loc.get('past')))
        original_forms=set().union(*(rv._forms(t) for t in rv._tokens(rv._normalise(original))))
        print('NEW_CONTENT_TOKENS',repr([w for w in loc['content'] if not rv._forms(w)&original_forms]))
        matches=[]
        for source,past,ctx in loc['sentences']:
            if rv._subsequence(loc['content'],source): matches.append({'source':source,'past':past,'scope':sorted(set(source)&rv._SCOPE),'context':sorted(ctx)})
        print('SUBSEQUENCE_MATCHING_WINDOWS',repr(matches))
    print('WORDS',len(rewrite.split()))
# Full requested source excerpts, copied exactly from files, with no reformatting.
sections=[
('backend/app/models/main.py', ['_appeal_client','improve_generated_appeal','_schedule_appeal_log','improve_appeal']),
('backend/app/models/appeal_generation_service.py',['_log_rejected_rewrite','_safe_rewrite','_call','repair']),
('backend/app/models/appeal_rewrite_validator.py',None),
('backend/app/models/appeal_guidance_service.py',None),
('backend/app/models/quality_service.py',None),
('backend/app/models/gemini_service.py',['score_text','call_gemini_with_key','_diagnose_weaknesses','_build_improvement_prompt','_fallback_improved_appeal','_is_weak_improvement','improve_appeal_text']),
('backend/app/models/appeal_improvement_selection.py',None),
('frontend/src/config/appealLengths.json',None)]
with (ROOT/'investigation_output/requested_source.txt').open('w',encoding='utf-8',newline='') as f:
    for p,names in sections:
        text=(ROOT/p).read_bytes().decode('utf-8')
        f.write('\n===== '+p+' =====\n')
        if names is None: f.write(text); continue
        lines=text.splitlines(keepends=True)
        if p.endswith('gemini_service.py'):
            tree=ast.parse(text)
            constant=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SYSTEM_INSTRUCTION' for t in n.targets))
            f.write(''.join(lines[constant.lineno-1:constant.end_lineno])+'\n')
        tree=ast.parse(text)
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
                start=min([node.lineno]+[d.lineno for d in node.decorator_list])
                f.write(''.join(lines[start-1:node.end_lineno])+'\n\n')
    f.write('\n===== frontend/src/pages/DonationAppealAnalyzer.jsx: improveAppeal =====\n')
    js=(ROOT/'frontend/src/pages/DonationAppealAnalyzer.jsx').read_bytes().decode('utf-8')
    start=js.index('async function improveAppeal(')
    end=js.index('\n}',start)+2
    f.write(js[start:end])
