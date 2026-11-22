"""Lê a planilha de produção de OTB (OneDrive) e gera {data: {data, vias:[...], equipes:[...]}}.
Uso: python3 importar_otb.py <planilha.xlsx> <saida.json>
Só o nome das vias vai para o painel (sem medidas)."""
import sys, json, re, datetime as dt, openpyxl, unicodedata

def chave(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\s+', ' ', s).strip()
    return re.sub(r'^(rua|r\.|avenida|av\.) ', '', s)

def bonito(s):
    s = re.sub(r'[\[\]]', '', re.sub(r'\s+', ' ', str(s))).strip(' .,;-')
    peq = {'de', 'da', 'do', 'das', 'dos', 'e'}
    out = []
    for i, w in enumerate(s.split(' ')):
        if i and w.lower() in peq: out.append(w.lower())
        elif w.islower() or (w.isupper() and len(w) > 3): out.append(w[:1].upper() + w[1:].lower())
        else: out.append(w)
    s = ' '.join(out)
    s = re.sub(r'^Mg ', 'MG-', s)
    # sem tipo de via na frente: é rua (ex.: "Dom Joaquim" -> "Rua Dom Joaquim")
    if not re.match(r'(?i)(rua|r\.|travessa|tv\.|avenida|av\.|beco|estrada|rodovia|mg|lmg|br|pra[cç]a|alameda|trevo|ponte|largo|vila|distrito)\b', s):
        s = 'Rua ' + s
    return s

wb = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)
ws = wb['Produção Diária OTB']
hdr = None; dias = {}
for row in ws.iter_rows(values_only=True):
    if hdr is None:
        if row and 'Data' in row and 'Rua' in row:
            hdr = {str(v).strip(): i for i, v in enumerate(row) if v is not None}
        continue
    d = row[hdr['Data']] if hdr['Data'] < len(row) else None
    rua = row[hdr['Rua']] if hdr['Rua'] < len(row) else None
    if not isinstance(d, (dt.date, dt.datetime)) or not rua or not str(rua).strip():
        continue
    tipo = str(row[hdr['Tipo']] or '').strip() if 'Tipo' in hdr else ''
    eq = str(row[hdr['Equipe']] or '').strip() if 'Equipe' in hdr else ''
    k = d.strftime('%Y-%m-%d')
    dia = dias.setdefault(k, {'data': k, 'vias': [], 'equipes': [], '_k': set()})
    nome = bonito(rua)
    if not nome or chave(nome).startswith('obs'):
        continue
    if tipo and 'quebra' in tipo.lower():
        nome += ' (quebra-molas)'
    ck = chave(nome)
    if ck not in dia['_k']:
        dia['_k'].add(ck); dia['vias'].append(nome)
    else:  # mesma via escrita de outro jeito: fica a forma mais completa
        for j, v in enumerate(dia['vias']):
            if chave(v) == ck and len(nome) > len(v): dia['vias'][j] = nome
    m = re.search(r'\(([^)]+)\)', eq); eqn = m.group(1).strip() if m else eq
    if eqn and eqn not in dia['equipes']:
        dia['equipes'].append(eqn)
for v in dias.values():
    v.pop('_k')
json.dump(dict(sorted(dias.items())), open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
print(len(dias), 'dias,', sum(len(v['vias']) for v in dias.values()), 'vias')
