-- upgrade --
CREATE TABLE IF NOT EXISTS "voice_channels" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "owner_id" BIGINT NOT NULL,
    "sequence" INT NOT NULL  DEFAULT 0,
    "channel_id" BIGINT NOT NULL,
    "type" VARCHAR(10) NOT NULL  DEFAULT 'normal'
);
COMMENT ON COLUMN "voice_channels"."type" IS 'normal: normal\nsequential: sequential\npredefined: predefined\ncloned: cloned';;
CREATE TABLE IF NOT EXISTS "guild_config" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "prefix" VARCHAR(3) NOT NULL
);;
DROP TABLE IF EXISTS "voice_channels";
-- downgrade --
DROP TABLE IF EXISTS "voice_channels";
DROP TABLE IF EXISTS "guild_config";
