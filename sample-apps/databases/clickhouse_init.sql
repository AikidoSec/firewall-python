CREATE TABLE IF NOT EXISTS dogs (
    id UUID DEFAULT generateUUIDv4(),
    dog_name String,
    isAdmin UInt8
) ENGINE = MergeTree()
ORDER BY id;
