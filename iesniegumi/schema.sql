-- «Iesniegumi» · datubāzes shēma (SQLite). Dati sintētiski.

CREATE TABLE IF NOT EXISTS temas (
    id        INTEGER PRIMARY KEY,
    nosaukums TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS iesniegumi (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    numurs            TEXT    NOT NULL UNIQUE,              -- 2026-0001
    izveidots         TEXT    NOT NULL,                     -- ISO laiks (UTC)
    vards             TEXT    NOT NULL,
    epasts            TEXT    NOT NULL,
    tema_id           INTEGER NOT NULL REFERENCES temas(id),
    vieta             TEXT    NOT NULL,
    apraksts          TEXT    NOT NULL,
    piekrisana        INTEGER NOT NULL CHECK (piekrisana = 1),
    statuss           TEXT    NOT NULL DEFAULT 'Jauns'
                      CHECK (statuss IN ('Jauns', 'Apstrādē', 'Atbildēts', 'Noraidīts')),
    atbilde           TEXT,                                 -- nosūtītā atbilde vai noraidījuma pamatojums
    atbildes_projekts TEXT,                                 -- darbinieka melnraksts (arī no MI ieteikuma)
    slegts            TEXT                                  -- kad statuss kļuva Atbildēts/Noraidīts
);

CREATE TABLE IF NOT EXISTS notikumi (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    iesniegums_id  INTEGER NOT NULL REFERENCES iesniegumi(id) ON DELETE CASCADE,
    laiks          TEXT    NOT NULL,
    loma           TEXT    NOT NULL,                        -- iedzivotajs / darbinieks / vaditajs / sistema
    veids          TEXT    NOT NULL,                        -- iesniegts / statuss / komentars / mi_izmantots / mi_tema
    apraksts       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_iesniegumi_statuss ON iesniegumi(statuss);
CREATE INDEX IF NOT EXISTS idx_notikumi_iesniegums ON notikumi(iesniegums_id);

INSERT OR IGNORE INTO temas (id, nosaukums) VALUES
    (1, 'Ceļi un bedres'),
    (2, 'Ielu apgaismojums'),
    (3, 'Atkritumi'),
    (4, 'Bērnudārza rinda'),
    (5, 'Sociālā palīdzība'),
    (6, 'Cits');
