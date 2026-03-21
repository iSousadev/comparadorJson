"""
app_comparador.py — Frontend Flask para o Comparador de Gabaritos
Uso: python app_comparador.py
Acesse: http://localhost:5000
"""

import json
import re
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

TOTAL_QUESTIONS = 60
COLS_PER_PAGE = 4
QUESTIONS_PER_COL = TOTAL_QUESTIONS // COLS_PER_PAGE
OPTIONS = 5
LETTERS = "ABCDE"


def parsear_txt(texto):
    """
    Extrai anuladas do Comparador_Json_*.txt.
    Retorna dict: {(pagina, coluna, questao): letras}
    Ex: {(1, 2, 5): "BC"}
    """
    anuladas = {}
    # Linha exemplo: - [Aviso] pagina 1 coluna 1 questão 2 anulada por multiplas marcações (BC)
    pattern = re.compile(
        r"pagina\s+(\d+)\s+coluna\s+(\d+)\s+quest[aã]o\s+(\d+)\s+anulada[^(]+\(([A-E]+)\)",
        re.IGNORECASE
    )
    for match in pattern.finditer(texto):
        pag, col, q, letras = int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4)
        anuladas[(pag, col, q)] = letras
    return anuladas


def analisar_json(data, anuladas_txt=None):
    """Processa o JSON do gabarito e retorna os resultados estruturados.
    anuladas_txt: dict {(pag, col, q): letras} vindo do .txt (opcional)
    """
    resultado = data.get("resultado", [])
    arquivo = data.get("nome_do_arquivo", "N/A")
    gabarito_id = data.get("id", "N/A")

    pages = {}
    for item in resultado:
        pag = item.get("pagina")
        col = item.get("coluna")
        if not isinstance(pag, int) or not isinstance(col, int):
            continue
        pages.setdefault(pag, {})
        pages[pag][col] = item

    ok_list = []
    anuladas_list = []
    branco_list = []
    blank_41_60 = 0

    for pag in sorted(pages.keys()):
        cols = pages[pag]
        for col in sorted(cols.keys()):
            info = cols[col]
            matricula = info.get("matricula", "?")
            respostas = info.get("respostas", [])
            for resp in respostas:
                q = resp.get("questao")
                vec = resp.get("resposta_vetorial", [])
                if not isinstance(q, int) or len(vec) != OPTIONS:
                    continue
                json_sum = sum(vec)

                # Verifica se o .txt marcou esta questão como anulada
                chave = (pag, col, q)
                letras_txt = anuladas_txt.get(chave) if anuladas_txt else None

                if letras_txt:
                    # Anulada confirmada pelo .txt — usa as letras do txt
                    anuladas_list.append({
                        "pagina": pag,
                        "coluna": col,
                        "questao": q,
                        "letras": letras_txt,
                        "matricula": matricula,
                    })
                elif json_sum == 1:
                    letter = LETTERS[vec.index(1)]
                    ok_list.append({
                        "pagina": pag,
                        "coluna": col,
                        "questao": q,
                        "letra": letter,
                        "matricula": matricula,
                    })
                elif json_sum == 0:
                    if q <= 40:
                        branco_list.append({
                            "pagina": pag,
                            "coluna": col,
                            "questao": q,
                            "matricula": matricula,
                        })
                    else:
                        blank_41_60 += 1
                elif json_sum > 1:
                    letters = "".join(LETTERS[i] for i, v in enumerate(vec) if v == 1)
                    anuladas_list.append({
                        "pagina": pag,
                        "coluna": col,
                        "questao": q,
                        "letras": letters,
                        "matricula": matricula,
                    })

    total_paginas = len(pages)

    ok_list.sort(key=lambda x: (x["pagina"], x["coluna"], x["questao"]))
    anuladas_list.sort(key=lambda x: (x["pagina"], x["coluna"], x["questao"]))
    branco_list.sort(key=lambda x: (x["pagina"], x["coluna"], x["questao"]))

    return {
        "arquivo": arquivo,
        "gabarito_id": gabarito_id,
        "total_paginas": total_paginas,
        "ok": ok_list,
        "anuladas": anuladas_list,
        "branco": branco_list,
        "blank_41_60": blank_41_60,
        "total_ok": len(ok_list),
        "total_anuladas": len(anuladas_list),
        "total_branco": len(branco_list),
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OMR — Comparador de Gabaritos</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0e0e0f;
    --surface: #161618;
    --surface2: #1e1e21;
    --border: #2a2a2e;
    --text: #e8e6e1;
    --muted: #6b6a66;
    --green: #4ade80;
    --green-dim: #16532d;
    --red: #f87171;
    --red-dim: #5a1d1d;
    --amber: #fbbf24;
    --amber-dim: #5c3d0a;
    --blue: #60a5fa;
    --purple: #a78bfa;
    --mono: 'JetBrains Mono', monospace;
    --sans: 'Poppins', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
  }

  /* HEADER */
  .header {
    border-bottom: 1px solid var(--border);
    padding: 20px 32px;
    display: flex;
    align-items: center;
    gap: 16px;
    background: var(--surface);
  }
  .header-badge {
    background: var(--purple);
    color: #1a0a40;
    font-family: var(--mono);
    font-weight: 700;
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 6px;
    letter-spacing: 1px;
  }
  .header-title {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
  .header-sub {
    font-size: 12px;
    color: var(--muted);
    font-family: var(--mono);
    margin-left: auto;
  }

  /* UPLOAD ZONE */
  .upload-zone {
    max-width: 640px;
    margin: 80px auto;
    padding: 0 24px;
  }
  .upload-title {
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 8px;
    letter-spacing: -1px;
  }
  .upload-sub {
    color: var(--muted);
    font-family: var(--mono);
    font-size: 13px;
    margin-bottom: 40px;
  }

  .drop-area {
    border: 2px dashed var(--border);
    border-radius: 16px;
    padding: 60px 40px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: var(--surface);
  }
  .drop-area:hover, .drop-area.drag-over {
    border-color: var(--purple);
    background: #1a1520;
  }
  .drop-icon {
    font-size: 40px;
    margin-bottom: 16px;
    display: block;
  }
  .drop-text {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .drop-hint {
    font-size: 12px;
    color: var(--muted);
    font-family: var(--mono);
  }
  #file-input { display: none; }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--purple);
    color: #1a0a40;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.2s;
    margin-top: 24px;
    width: 100%;
    justify-content: center;
  }
  .btn:hover { opacity: 0.85; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  /* LOADING */
  .loading {
    display: none;
    text-align: center;
    padding: 40px;
    font-family: var(--mono);
    color: var(--muted);
    font-size: 13px;
  }
  .spinner {
    width: 32px; height: 32px;
    border: 2px solid var(--border);
    border-top-color: var(--purple);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 16px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* RESULTS */
  .results { display: none; padding: 32px; max-width: 1400px; margin: 0 auto; }

  .result-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 32px;
    flex-wrap: wrap;
    gap: 16px;
  }
  .result-title {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
  .result-meta {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--muted);
    margin-top: 4px;
  }
  .btn-reset {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 8px 16px;
    border-radius: 8px;
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }
  .btn-reset:hover { background: var(--border); }

  /* STAT CARDS */
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 32px;
  }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }
  .stat-label {
    font-size: 11px;
    font-family: var(--mono);
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }
  .stat-value {
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1;
  }
  .stat-ok .stat-value { color: var(--green); }
  .stat-anuladas .stat-value { color: var(--red); }
  .stat-branco .stat-value { color: var(--amber); }
  .stat-info .stat-value { color: var(--blue); }

  /* TABS */
  .tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 4px;
    width: fit-content;
  }
  .tab {
    padding: 8px 20px;
    border-radius: 7px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    background: transparent;
    color: var(--muted);
    font-family: var(--sans);
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .tab.active { background: var(--surface2); color: var(--text); }
  .tab .count {
    font-family: var(--mono);
    font-size: 11px;
    padding: 1px 6px;
    border-radius: 4px;
    background: var(--border);
  }
  .tab-ok.active .count { background: var(--green-dim); color: var(--green); }
  .tab-anuladas.active .count { background: var(--red-dim); color: var(--red); }
  .tab-branco.active .count { background: var(--amber-dim); color: var(--amber); }

  /* FILTER BAR */
  .filter-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    align-items: center;
    flex-wrap: wrap;
  }
  .filter-input {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 14px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    outline: none;
    width: 200px;
    transition: border-color 0.2s;
  }
  .filter-input:focus { border-color: var(--purple); }
  .filter-label {
    font-size: 12px;
    color: var(--muted);
    font-family: var(--mono);
  }

  /* CARDS GRID */
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    transition: border-color 0.15s;
  }
  .card:hover { border-color: var(--muted); }

  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
  }
  .card-questao {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
    line-height: 1;
  }
  .card-badge {
    font-family: var(--mono);
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 5px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .badge-ok { background: var(--green-dim); color: var(--green); }
  .badge-anulada { background: var(--red-dim); color: var(--red); }
  .badge-branco { background: var(--amber-dim); color: var(--amber); }

  .card-letter {
    font-size: 32px;
    font-weight: 800;
    font-family: var(--mono);
    margin: 4px 0 8px;
  }
  .letter-ok { color: var(--green); }
  .letter-anulada { color: var(--red); }
  .letter-branco { color: var(--amber); }

  .card-meta {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  /* EMPTY STATE */
  .empty {
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
    font-family: var(--mono);
    font-size: 13px;
  }

  .footer {
    border-top: 1px solid var(--border);
    padding: 20px 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--surface);
    margin-top: 60px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .footer-left {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--muted);
  }
  .footer-left span {
    color: var(--green);
    font-weight: 700;
  }
  .footer-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .footer-link {
    font-family: var(--mono);
    font-size: 11px;
    color: white;
    text-decoration: none;
    transition: color 0.2s;
  }
  .footer-link:hover { color: var(--purple); }
  .footer-dot {
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--border);
  }
  .selected-file {
    display: none;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 16px;
    font-family: var(--mono);
    font-size: 13px;
    color: var(--text);
    align-items: center;
    gap: 10px;
  }
  .selected-file.show { display: flex; }
  .file-icon { color: var(--purple); font-size: 16px; }
  .file-name { flex: 1; }
  .file-size { color: var(--muted); font-size: 11px; }
</style>
</head>
<body>

<div class="header">
  <span class="header-badge">OMR</span>
  <span class="header-title">Comparador de Gabaritos</span>
</div>

<!-- UPLOAD -->
<div class="upload-zone" id="upload-section">
  <div class="upload-title">Verificar Gabarito</div>
  <div class="upload-sub">// Carregue o graded_result.json gerado pelo processador</div>

  <div class="drop-area" id="drop-area" onclick="document.getElementById('file-input').click()">
    <span class="drop-icon">📄</span>
    <div class="drop-text">Solte o arquivo JSON aqui</div>
    <div class="drop-hint">ou clique para selecionar · graded_result.json</div>
  </div>

  <input type="file" id="file-input" accept=".json">

  <div class="selected-file" id="selected-file">
    <span class="file-icon">✓</span>
    <span class="file-name" id="file-name-text">—</span>
    <span class="file-size" id="file-size-text">—</span>
  </div>

  <div class="drop-area" id="drop-area-txt" style="margin-top:12px;padding:30px 40px" onclick="document.getElementById('file-input-txt').click()">
    <span class="drop-icon" style="font-size:28px">📋</span>
    <div class="drop-text" style="font-size:14px">Relatório do comparador <span style="color:var(--muted);font-size:12px">(opcional)</span></div>
    <div class="drop-hint">Comparador_Json_*.txt — para identificar anuladas com as letras</div>
  </div>

  <input type="file" id="file-input-txt" accept=".txt">

  <div class="selected-file" id="selected-file-txt">
    <span class="file-icon" style="color:var(--amber)">✓</span>
    <span class="file-name" id="file-name-txt-text">—</span>
    <span class="file-size" id="file-size-txt-text">—</span>
  </div>

  <button class="btn" id="btn-analisar" disabled onclick="analisar()">
    Analisar Gabarito
  </button>
</div>

<!-- LOADING -->
<div class="loading" id="loading">
  <div class="spinner"></div>
  Processando JSON...
</div>

<!-- RESULTS -->
<div class="results" id="results">

  <div class="result-header">
    <div>
      <div class="result-title" id="result-title">—</div>
      <div class="result-meta" id="result-meta">—</div>
    </div>
    <button class="btn-reset" onclick="resetar()">← Novo arquivo</button>
  </div>

  <div class="stats">
    <div class="stat-card stat-ok">
      <div class="stat-label">Marcadas com sucesso</div>
      <div class="stat-value" id="stat-ok">0</div>
    </div>
    <div class="stat-card stat-anuladas">
      <div class="stat-label">Anuladas</div>
      <div class="stat-value" id="stat-anuladas">0</div>
    </div>
    <div class="stat-card stat-branco">
      <div class="stat-label">Em branco (Q1-40)</div>
      <div class="stat-value" id="stat-branco">0</div>
    </div>
    <div class="stat-card stat-info">
      <div class="stat-label">Páginas</div>
      <div class="stat-value" id="stat-paginas">0</div>
    </div>
  </div>

  <div class="tabs">
    <button class="tab tab-ok active" onclick="switchTab('ok')">
      Marcadas <span class="count" id="tab-count-ok">0</span>
    </button>
    <button class="tab tab-anuladas" onclick="switchTab('anuladas')">
      Anuladas <span class="count" id="tab-count-anuladas">0</span>
    </button>
    <button class="tab tab-branco" onclick="switchTab('branco')">
      Em Branco <span class="count" id="tab-count-branco">0</span>
    </button>
  </div>

  <div class="filter-bar">
    <span class="filter-label">filtrar:</span>
    <input class="filter-input" id="filter-pagina" placeholder="página..." oninput="filtrar()" type="number" min="1">
    <input class="filter-input" id="filter-questao" placeholder="questão..." oninput="filtrar()" type="number" min="1" max="60">
    <input class="filter-input" id="filter-matricula" placeholder="matrícula..." oninput="filtrar()" style="width:180px">
  </div>

  <div class="tab-panel active" id="panel-ok">
    <div class="cards-grid" id="grid-ok"></div>
  </div>
  <div class="tab-panel" id="panel-anuladas">
    <div class="cards-grid" id="grid-anuladas"></div>
  </div>
  <div class="tab-panel" id="panel-branco">
    <div class="cards-grid" id="grid-branco"></div>
  </div>

</div>

<script>
let dadosGlobal = null;
let tabAtual = 'ok';
let fileData = null;
let txtData = null;

// DRAG & DROP JSON
const dropArea = document.getElementById('drop-area');
dropArea.addEventListener('dragover', e => { e.preventDefault(); dropArea.classList.add('drag-over'); });
dropArea.addEventListener('dragleave', () => dropArea.classList.remove('drag-over'));
dropArea.addEventListener('drop', e => {
  e.preventDefault();
  dropArea.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) handleFile(f);
});

// DRAG & DROP TXT
const dropAreaTxt = document.getElementById('drop-area-txt');
dropAreaTxt.addEventListener('dragover', e => { e.preventDefault(); dropAreaTxt.classList.add('drag-over'); });
dropAreaTxt.addEventListener('dragleave', () => dropAreaTxt.classList.remove('drag-over'));
dropAreaTxt.addEventListener('drop', e => {
  e.preventDefault();
  dropAreaTxt.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) handleTxt(f);
});

document.getElementById('file-input').addEventListener('change', e => {
  if (e.target.files[0]) handleFile(e.target.files[0]);
});

document.getElementById('file-input-txt').addEventListener('change', e => {
  if (e.target.files[0]) handleTxt(e.target.files[0]);
});

function handleFile(f) {
  if (!f.name.endsWith('.json')) { alert('Selecione um arquivo .json'); return; }
  const reader = new FileReader();
  reader.onload = ev => {
    fileData = ev.target.result;
    document.getElementById('file-name-text').textContent = f.name;
    document.getElementById('file-size-text').textContent = (f.size / 1024).toFixed(1) + ' KB';
    document.getElementById('selected-file').classList.add('show');
    document.getElementById('btn-analisar').disabled = false;
  };
  reader.readAsText(f);
}

function handleTxt(f) {
  if (!f.name.endsWith('.txt')) { alert('Selecione um arquivo .txt'); return; }
  const reader = new FileReader();
  reader.onload = ev => {
    txtData = ev.target.result;
    document.getElementById('file-name-txt-text').textContent = f.name;
    document.getElementById('file-size-txt-text').textContent = (f.size / 1024).toFixed(1) + ' KB';
    document.getElementById('selected-file-txt').classList.add('show');
  };
  reader.readAsText(f);
}

function analisar() {
  if (!fileData) return;
  try { JSON.parse(fileData); }
  catch(e) { alert('JSON inválido: ' + e.message); return; }

  document.getElementById('upload-section').style.display = 'none';
  document.getElementById('loading').style.display = 'block';

  const payload = { json_data: JSON.parse(fileData) };
  if (txtData) payload.txt_data = txtData;

  fetch('/analisar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    dadosGlobal = data;
    renderizar(data);
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';
  })
  .catch(err => {
    alert('Erro ao analisar: ' + err);
    resetar();
  });
}

function renderizar(d) {
  document.getElementById('result-title').textContent = d.arquivo || 'Gabarito';
  document.getElementById('result-meta').textContent =
    `ID: ${d.gabarito_id} · ${d.total_paginas} páginas · gerado em ${d.gerado_em}`;

  document.getElementById('stat-ok').textContent = d.total_ok;
  document.getElementById('stat-anuladas').textContent = d.total_anuladas;
  document.getElementById('stat-branco').textContent = d.total_branco;
  document.getElementById('stat-paginas').textContent = d.total_paginas;

  document.getElementById('tab-count-ok').textContent = d.total_ok;
  document.getElementById('tab-count-anuladas').textContent = d.total_anuladas;
  document.getElementById('tab-count-branco').textContent = d.total_branco;

  renderGrid('ok', d.ok, 'ok');
  renderGrid('anuladas', d.anuladas, 'anulada');
  renderGrid('branco', d.branco, 'branco');
}

function renderGrid(tipo, items, badgeTipo) {
  const grid = document.getElementById('grid-' + tipo);
  if (!items || items.length === 0) {
    grid.innerHTML = '<div class="empty">Nenhum item nesta categoria.</div>';
    return;
  }
  const badge = badgeTipo === 'ok' ? 'OK' : badgeTipo === 'anulada' ? 'ANULADA' : 'BRANCO';
  const badgeClass = `badge-${badgeTipo === 'anulada' ? 'anulada' : badgeTipo === 'branco' ? 'branco' : 'ok'}`;
  const letterClass = `letter-${badgeTipo === 'anulada' ? 'anulada' : badgeTipo === 'branco' ? 'branco' : 'ok'}`;

  grid.innerHTML = items.map(item => {
    const display = badgeTipo === 'ok' ? item.letra : badgeTipo === 'anulada' ? item.letras : '—';
    return `<div class="card" data-pagina="${item.pagina}" data-questao="${item.questao}" data-matricula="${item.matricula || ''}">
      <div class="card-top">
        <div class="card-questao">Q${item.questao}</div>
        <span class="card-badge ${badgeClass}">${badge}</span>
      </div>
      <div class="card-letter ${letterClass}">${display}</div>
      <div class="card-meta">
        <span>Pág ${item.pagina} · Col ${item.coluna}</span>
        <span>${item.matricula || '—'}</span>
      </div>
    </div>`;
  }).join('');
}

function switchTab(tab) {
  tabAtual = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.tab-${tab}`).classList.add('active');
  document.getElementById(`panel-${tab}`).classList.add('active');
  filtrar();
}

function filtrar() {
  const pag = document.getElementById('filter-pagina').value.trim();
  const q = document.getElementById('filter-questao').value.trim();
  const mat = document.getElementById('filter-matricula').value.trim().toLowerCase();
  const cards = document.querySelectorAll(`#grid-${tabAtual} .card`);
  cards.forEach(card => {
    const matchPag = !pag || card.dataset.pagina === pag;
    const matchQ = !q || card.dataset.questao === q;
    const matchMat = !mat || card.dataset.matricula.toLowerCase().includes(mat);
    card.style.display = matchPag && matchQ && matchMat ? '' : 'none';
  });
}

function resetar() {
  dadosGlobal = null;
  fileData = null;
  txtData = null;
  document.getElementById('upload-section').style.display = 'block';
  document.getElementById('loading').style.display = 'none';
  document.getElementById('results').style.display = 'none';
  document.getElementById('selected-file').classList.remove('show');
  document.getElementById('selected-file-txt').classList.remove('show');
  document.getElementById('btn-analisar').disabled = true;
  document.getElementById('file-input').value = '';
  document.getElementById('file-input-txt').value = '';
  document.getElementById('filter-pagina').value = '';
  document.getElementById('filter-questao').value = '';
  document.getElementById('filter-matricula').value = '';
  switchTab('ok');
}
</script>

<footer class="footer">
  <div class="footer-left">
    Desenvolvido por <span><a class="footer-link" href="https://github.com/iSousadev" target="_blank">iSousadev</a></span> — 2026
  </div>
  <div class="footer-right">
  </div>
</footer>

</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/analisar", methods=["POST"])
def analisar():
    try:
        payload = request.get_json(force=True)
        if not payload or "json_data" not in payload:
            return jsonify({"erro": "JSON não enviado"}), 400
        data = payload["json_data"]
        txt_str = payload.get("txt_data", "")
        anuladas_txt = parsear_txt(txt_str) if txt_str.strip() else None
        resultado = analisar_json(data, anuladas_txt)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  OMR — Comparador de Gabaritos")
    print("  Acesse: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, port=5000)