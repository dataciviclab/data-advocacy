# Anagrafica Mapping — source_id SO ↔ IPA

La `data/anagrafica_enti.json` collega i `source_id` del Source Observatory
agli enti pubblici censiti in IPA (IndicePA). Questo mapping serve per:

- **Trovare PEC ufficiali** da usare per FOIA e segnalazioni
- **Validare** i contatti già raccolti manualmente
- **Scoprire** nuovi enti da aggiungere al monitoraggio

## Struttura dell'anagrafica

```json
{
  "source_id": "mit_opendata",
  "nome": "Ministero delle Infrastrutture e dei Trasporti",
  "tipo": "MINISTERO",
  "sito": "https://dati.mit.gov.it",
  "codice_ipa": "m_inf",
  "contatti": {
    "urp_email": "urp@mit.gov.it",
    "pec": "protocollo@pec.mit.gov.it",
    "ipa_pec": "m_inf@pec.mit.gov.it",
    "rpct_email": "",
    "urp_url": "",
    "note": "..."
  },
  "note": "..."
}
```

| Campo | Descrizione |
|---|---|
| `source_id` | Identificativo usato da SO e nel Lab |
| `codice_ipa` | Codice univoco IPA dell'ente (null se non mappato) |
| `contatti.pec` | PEC di protocollo/contatto (per invio FOIA) |
| `contatti.ipa_pec` | PEC ufficiale registrata in IPA (per verifica) |

## Come trovare il codice IPA di un ente

Il dataset IPA è un support_dataset in `dataset-incubator`, disponibile
come parquet su GCS.

```bash
# 1. Query diretta sul parquet locale (se hai runnato la pipeline)
duckdb -c "
SELECT codice_ipa, denominazione_ente, mail1, tipo_mail1
FROM read_parquet('dataset-incubator/out/data/mart/ipa_enti/2026/ipa_enti.parquet')
WHERE denominazione_ente ILIKE '%ministero%salute%'
AND tipologia = 'Pubbliche Amministrazioni'
"
```

```bash
# 2. Oppure via API CKAN di IPA
curl -s "https://indicepa.gov.it/ipa-dati/api/3/action/datastore_search?resource_id=d09adf99-dc10-4349-8c53-27b1e5aa97b6&q=Ministero+Salute&limit=3"
```

## Regole per il mapping

1. **Cerca per denominazione esatta** partendo dal nome dell'ente
2. **Filtra per `tipologia = 'Pubbliche Amministrazioni'`** — scarta SA, GPS, SOC
3. **Preferisci la PEC** (`tipo_mail1 = 'Pec'`) su altri indirizzi
4. **Verifica il match** — controlla che non sia un falso positivo
   (es. "Comune di Anacapri" per ANAC, o "Comune di Villacidro" per ACI)
5. **Se non trovi**, prova con l'acronimo in `acronimo` o cerca in altre
   tipologie (es. Consip è "Societa' in Conto Economico Consolidato")

## Enti non mappabili

Alcuni source_id SO non corrispondono a enti PA in IPA:

| source_id | Motivo |
|---|---|
| `eligendo` | Portale storico elettorale, non ente |
| `noipa_sparql` | Sistema NoiPA, non ente autonomo |
| `openbdap` | Portale BDAP (MEF/RGS), non ente separato |
| `opencoesione` | Portale PCM, non ente |
| `terna_opendata` | Terna S.p.A., società quotata non in IPA come PA |

Questi enti rimangono in anagrafica con `codice_ipa: null`.

## Aggiornare il mapping

Quando un nuovo source_id viene aggiunto a SO:

1. Cerca l'ente in IPA seguendo le regole sopra
2. Aggiungi o aggiorna l'entry in `data/anagrafica_enti.json`
3. Includi `codice_ipa` e `ipa_pec` nei `contatti`
4. Se l'ente non è in IPA, setta `codice_ipa: null`

```bash
# Verifica che il JSON sia valido
python3 -m json.tool data/anagrafica_enti.json > /dev/null

# Verifica che tutti i source_id siano unici
python3 -c "
import json
d = json.load(open('data/anagrafica_enti.json'))
ids = [e['source_id'] for e in d]
assert len(ids) == len(set(ids)), 'source_id duplicati!'
print(f'OK: {len(d)} enti, {sum(1 for e in d if e.get(\"codice_ipa\"))} con IPA')
"
```
