-- upgrade --
ALTER TABLE "member_config" ALTER COLUMN "bitrate" SET DEFAULT 64000;
ALTER TABLE "member_config" ALTER COLUMN "bitrate" SET NOT NULL;
-- downgrade --
ALTER TABLE "member_config" ALTER COLUMN "bitrate" DROP NOT NULL;
ALTER TABLE "member_config" ALTER COLUMN "bitrate" DROP DEFAULT;
