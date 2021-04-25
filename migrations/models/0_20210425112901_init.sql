-- upgrade --
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "voice_channels" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "owner_id" BIGINT NOT NULL,
    "sequence" INT NOT NULL  DEFAULT 0,
    "channel_id" BIGINT NOT NULL,
    "type" VARCHAR(10) NOT NULL  DEFAULT 'normal'
);
COMMENT ON COLUMN "voice_channels"."type" IS 'normal: normal\nsequential: sequential\npredefined: predefined\ncloned: cloned';
CREATE TABLE IF NOT EXISTS "member_voice" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100),
    "limit" INT NOT NULL  DEFAULT 0,
    "bitrate" INT
);
CREATE TABLE IF NOT EXISTS "voice_config" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "name" VARCHAR(100),
    "limit" INT NOT NULL  DEFAULT 0,
    "type" VARCHAR(10) NOT NULL  DEFAULT 'normal'
);
COMMENT ON COLUMN "voice_config"."type" IS 'normal: normal\nsequential: sequential\npredefined: predefined\ncloned: cloned';
