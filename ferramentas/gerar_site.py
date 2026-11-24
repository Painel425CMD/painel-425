#!/usr/bin/env python3
"""Gera a versão pública (só leitura) do Painel de Frentes – Contrato 425.

Uso: python3 gerar_site.py dados.json saida/index.html
dados.json = {"frentes": {...}, "eventos": {...}, "pendencias": {...}, "pendhist": {...},
              "otb": {...}, "midia": {...}, "agenda": {...}}
(o conteúdo das coleções do painel, lido com db_list).
Remove telefones e e-mails antes de publicar.
Fotos: só entram as marcadas como "publico": true E que já tenham o arquivo
copiado em <repo>/fotos/<asset>.jpg|.png|.webp|.gif|.mp4|.webm (as rotinas copiam).
"""
import json, re, sys, datetime, os
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
FONE = re.compile(r'(\+?55[\s-]?)?\(?\b\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}\b')
MAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')

def limpa(v):
    if isinstance(v, str):
        v = MAIL.sub('[e-mail oculto]', v)
        return FONE.sub('[telefone oculto]', v)
    if isinstance(v, dict):
        return {k: limpa(x) for k, x in v.items()}
    if isinstance(v, list):
        return [limpa(x) for x in v]
    return v

def main(src, out):
    dados = limpa(json.load(open(src, encoding='utf-8')))
    for c in ('frentes', 'eventos', 'pendencias', 'pendhist', 'otb', 'midia', 'agenda', 'relatorios'):
        dados.setdefault(c, {})
    # fotos e vídeos: só as permitidas e já copiadas para a pasta fotos/ do site
    pasta = os.path.join(os.path.dirname(os.path.abspath(out)), 'fotos')
    tem = {os.path.splitext(f)[0]: f for f in (os.listdir(pasta) if os.path.isdir(pasta) else [])}
    pub = {}
    for k, v in dados['midia'].items():
        a = str(v.get('asset', ''))
        if v.get('publico') is True and a in tem:
            pub[k] = {**{x: v.get(x) for x in ('alvo', 'evento', 'asset', 'tipo', 'data', 'criadoEm', 'publico')}, 'nome': '', 'src': 'fotos/' + tem[a]}
    dados['midia'] = pub
    # agenda: só os itens marcados para o site público
    dados['agenda'] = {k: v for k, v in dados['agenda'].items() if v.get('publico') is not False}
    # relatórios diários: só os aprovados e publicados
    dados['relatorios'] = {k: v for k, v in dados['relatorios'].items() if v.get('publico') is True}
    # notas internas das pendências não vão para o site aberto
    dados['pendhist'] = {k: v for k, v in dados['pendhist'].items() if not v.get('interna')}
    agora = datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y às %Hh%M')
    shim = ('<meta name="robots" content="noindex,nofollow">\n<script>\nwindow.__PUBLIC__=' + json.dumps(agora) + ';\n'
            'window.__SNAP__=' + json.dumps(dados, ensure_ascii=False).replace('</', '<\\/') + ';\n'
            '(function(){const S=window.__SNAP__;'
            'const snap=c=>{const docs=Object.keys(S[c]||{}).map(id=>({id,exists:true,data:()=>S[c][id],metadata:{fromCache:false,hasPendingWrites:false}}));'
            'return {docs,size:docs.length,empty:!docs.length,metadata:{fromCache:false,hasPendingWrites:false},docChanges:()=>[]};};'
            'const ro=()=>Promise.reject({code:"invalid_argument",message:"somente leitura"});'
            'const db={collection:c=>({onSnapshot:n=>{setTimeout(()=>n(snap(c)),0);return()=>{}},doc:()=>({set:ro,update:ro,delete:ro})})};'
            'window.claude={use:async n=>n==="db"?db:n==="user"?{can:()=>false,isOwner:()=>false,canEdit:()=>false}:null};})();\n</script>\n')
    html = open(os.path.join(AQUI, 'modelo.html'), encoding='utf-8').read()
    html = html.replace('</head>', shim + '</head>', 1)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    print('ok', out, {c: len(dados[c]) for c in dados})

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
