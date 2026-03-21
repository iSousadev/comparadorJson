# Comparador de Gabaritos (OMR)

Aplicação web em Flask para visualizar e validar o `graded_result.json` gerado pelo processador OMR. O sistema lê o gabarito, classifica respostas como **OK**, **Anuladas** ou **Em branco** e exibe tudo em uma interface única com filtros por página, questão e matrícula. Também aceita, opcionalmente, um relatório `.txt` do comparador para identificar anuladas com as letras marcadas.

**Funcionalidades**
- Upload de `graded_result.json` via drag & drop ou seleção de arquivo
- Upload opcional de `Comparador_Json_*.txt` para validar anuladas
- Totais por categoria (OK, Anuladas, Em branco Q1–40) e número de páginas
- Cards por questão com filtros por página, questão e matrícula
- Interface toda embutida no Flask (HTML/CSS/JS no backend)

**Como funciona**
1. Você envia o `graded_result.json`.
2. (Opcional) Você envia o relatório `Comparador_Json_*.txt`.
3. O backend interpreta o JSON e cruza com o `.txt` (se existir).
4. O frontend renderiza estatísticas e cards filtráveis.

**Regras de classificação**
- **OK**: exatamente 1 marca na questão
- **Em branco**: 0 marcas na questão (somente Q1–40 são listadas)
- **Anulada**: mais de 1 marca
- **Anulada pelo TXT**: se o `.txt` indicar a questão como anulada, ela prevalece e as letras são as do relatório

**Formato esperado do JSON**
O arquivo deve seguir o esquema usado pelo processador OMR:

```json
{
  "nome_do_arquivo": "graded_result.json",
  "id": "ABC123",
  "resultado": [
    {
      "pagina": 1,
      "coluna": 1,
      "matricula": "0000001",
      "respostas": [
        { "questao": 1, "resposta_vetorial": [0,1,0,0,0] },
        { "questao": 2, "resposta_vetorial": [1,1,0,0,0] }
      ]
    }
  ]
}
```

**Formato esperado do TXT (opcional)**
O relatório deve conter linhas indicando anuladas no padrão:

```
pagina 1 coluna 1 questao 2 anulada por multiplas marcacoes (BC)
```

As letras entre parênteses são usadas para exibir quais alternativas estavam marcadas.

**Como rodar localmente**
1. Crie e ative um ambiente virtual.
2. Instale dependências.
3. Rode o servidor.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app_comparador.py
```

Acesse `http://localhost:5000`.

**Endpoints**
- `GET /` Interface web
- `POST /analisar` Recebe `{ json_data, txt_data? }` e retorna o resultado processado

**Deploy no Vercel**
Este repositório já possui `vercel.json` e `api/index.py` para rodar o Flask como função serverless:
- `api/index.py` expõe o objeto `app` do Flask
- `vercel.json` roteia todas as rotas para `api/index.py`

**Estrutura do projeto**
- `app_comparador.py` Backend Flask + frontend embutido
- `api/index.py` Entrypoint para Vercel
- `requirements.txt` Dependências Python
- `vercel.json` Configuração do Vercel

**É isso ai mesmo**
**quero um emprego**
**Batatinha quando nasce**
