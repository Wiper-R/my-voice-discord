TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "localhost",
                "port": "5432",
                "user": "postgres",
                "password": "postgres",
                "database": "myvoice",
                "maxsize": 10,
            },
        }
    },
    "apps": {
        "models": {
            "models": ("aerich.models", "models.voice", "models.member", "models.guild"),
            "default_connection": "default",
        },
    },
}

TOKEN = ""