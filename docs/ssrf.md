# Server-side request forgery (SSRF)

Aikido firewall secures your app against server-side request forgery (SSRF) attacks. SSRF vulnerabilities allow attackers to send crafted requests to internal services, bypassing firewalls and security controls. Runtime blocks SSRF attacks by intercepting and validating requests to internal services.

## Example

```
GET https://your-app.com/files?url=http://localhost:3000/private
```

```js
const response = http.request(req.query.url);
```

In this example, an attacker sends a request to `localhost:3000/private` from your server. Firewall can intercept the request and block it, preventing the attacker from accessing internal services.

```
GET https://your-app.com/files?url=http://localtest.me:3000/private
```

In this example, the attacker sends a request to `localtest.me:3000/private`, which resolves to `127.0.0.1`. Firewall can intercept the request and block it, preventing the attacker from accessing internal services.

We don't protect against stored SSRF attacks, where an attacker injects a malicious URL into your app's database. To prevent stored SSRF attacks, validate and sanitize user input before storing it in your database.

## Allowlisting your own hostnames (`AIKIDO_TRUSTED_HOSTNAMES`)

To safely allow outgoing requests to your own services, set the `AIKIDO_TRUSTED_HOSTNAMES` environment variable to a comma-separated list of your hostnames:

```
AIKIDO_TRUSTED_HOSTNAMES=myapp.com,api.myapp.com,backend.internal
```
Any outgoing request whose destination hostname exactly matches one of these values will not be flagged as SSRF

**When should you set this?**
Set `AIKIDO_TRUSTED_HOSTNAMES` when your application makes outgoing requests to its own domain, and those hostnames appear in user-supplied input (e.g. `Host`, `Referer`, `Origin`, etc.)

## Which built-in modules are protected?

Firewall protects against SSRF attacks in the following built-in modules:
* `http`
