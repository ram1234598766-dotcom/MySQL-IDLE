# Security notes

- The desktop app does not save the password entered into the connection dialog. SQL history is text history and can contain sensitive literals, so disable history in the source if that risk matters.
- The Android companion is disabled by default. It binds to local network interfaces only after explicit confirmation and uses a temporary pairing code, short-lived session tokens, rate-limited pairing attempts, host/origin checks, and 30-minute idle expiry.
- The companion currently uses plain HTTP. Pairing codes, SQL statements, query results, and database credentials transit the local network without application-layer encryption. Use only a trusted private LAN, never public Wi-Fi, and do not port-forward or expose the service to the internet. Use a trusted VPN/private tunnel for remote access.
- The server rejects unexpected Host headers and mismatched Host ports, checks browser origins on POST requests, limits JSON request bodies, and returns HTTP 413 when a request exceeds the body limit. Keep the desktop companion disabled when not in use.
- The companion intentionally accepts arbitrary SQL for an authenticated session. Pairing grants database privileges of the MySQL account entered on the phone. Prefer a dedicated least-privilege MySQL account.
- Stop the companion from the desktop when done. Stopping closes mobile MySQL sessions and removes temporary result files.
- Release executables built by the included workflow are unsigned unless the project owner separately configures a trusted code-signing certificate. Windows SmartScreen may show a warning for unsigned builds.
