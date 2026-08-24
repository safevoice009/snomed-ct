import re

js = open('static/app.js', encoding='utf-8').read() + open('static/scrub-engine.js', encoding='utf-8').read()
html = open('static/index.html', encoding='utf-8').read()

ids = sorted(set(re.findall(r'getElementById\([\'"]([^\'"]+)[\'"]\)', js)))
missing = [i for i in ids if not re.search(r'id=[\'"]' + re.escape(i) + '[\'"]', html)]
print('TOTAL IDS USED BY JS:', len(ids))
print('MISSING FROM HTML:', missing if missing else 'NONE')

classes = sorted(set(re.findall(r'(?:classList\.(?:add|remove|toggle|contains)|querySelector(?:All)?|getElementsByClassName|closest)\(\s*[\'"]\.?([\w\-]+)[\'"]', js)))
print('CLASSES/SELECTORS USED BY JS:', ', '.join(classes))
