PRAGMA foreign_keys = ON;

-- ========================
-- Items (basic definition)
-- ========================
CREATE TABLE items (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    short_name      TEXT,
    item_type       TEXT,
    weight          REAL
);

-- ========================
-- Weapons
-- ========================
CREATE TABLE weapons (
    item_id         TEXT PRIMARY KEY,
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- ========================
-- Weapon Slots
-- ========================
CREATE TABLE slots (
    id              TEXT PRIMARY KEY,
    weapon_id       TEXT NOT NULL,
    name            TEXT NOT NULL,
    required        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (weapon_id) REFERENCES weapons(item_id)
);

-- ========================
-- Slot -> Allowed Items
-- ========================
CREATE TABLE slot_items (
    slot_id         TEXT NOT NULL,
    item_id         TEXT NOT NULL,
    PRIMARY KEY (slot_id, item_id),
    FOREIGN KEY (slot_id) REFERENCES slots(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- ========================
-- Conflicts (simplified)
-- ========================
CREATE TABLE conflicts (
    item_a          TEXT NOT NULL,
    item_b          TEXT NOT NULL,
    PRIMARY KEY (item_a, item_b),
    FOREIGN KEY (item_a) REFERENCES items(id),
    FOREIGN KEY (item_b) REFERENCES items(id)
);