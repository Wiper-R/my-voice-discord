-- upgrade --
CREATE TABLE IF NOT EXISTS "member_config" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100),
    "limit" INT NOT NULL  DEFAULT 0,
    "bitrate" INT
);;
DROP TABLE IF EXISTS "member_voice";
-- downgrade --
DROP TABLE IF EXISTS "member_config";
