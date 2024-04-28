# Tunnels-Backend

A Backend For [Tunnel Dashboard](https://github.com/Darren-project/tunnel-dashboard)

Systemd service's WorkingDirectory must point to repo root

# New Setup

1. Setup a turso database and complete creds.py

2. Fill Up and Run this sql command

```sql
CREATE TABLE settings (
   setting TEXT PRIMARY KEY,
   value TEXT
);

CREATE TABLE auth_control (
   endpoint TEXT PRIMARY KEY,
   permission TEXT
);

CREATE TABLE mapping (
   name TEXT PRIMARY KEY,
   host TEXT,
   target TEXT
);

INSERT INTO auth_control (endpoint. permission)
VALUES ('tunnels', 'private');

INSERT INTO settings ( setting, value ) VALUES
( 'client_id', 'xxx' ), ( 'jwks_url', 'https://authserver/oauth2/default/v1/keys' ), ('audience', 'api://default'), ('issuer', 'https://authserver/oauth2/default'), ('socks', '127.0.0.1:1055');

```

# Migration
1. Check if there's a newer sql file in the db under upgrade dir
2. If yes apply it then clone repo and restart server
