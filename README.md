![Aikido Firewall for Python 3](./docs/banner.svg)

# Aikido Firewall for Python 3

Aikido Firewall is an embedded Web Application Firewall that autonomously protects your Python apps against common and critical attacks.

It protects your Python apps by preventing user input containing dangerous strings, which allow SQL injections. It runs on the same server as your python app for simple [installation](#installation) and zero maintenance.

## Features

Firewall autonomously protects your Python applications against:

* 🛡️ [NoSQL injection attacks](https://www.aikido.dev/blog/web-application-security-vulnerabilities)
* 🛡️ [SQL injection attacks]([https://www.aikido.dev/blog/web-application-security-vulnerabilities](https://owasp.org/www-community/attacks/SQL_Injection))

Firewall operates autonomously on the same server as your Python app to:

* ✅ Secure your app like a classic web application firewall (WAF), but with none of the infrastructure or cost.

## Supported libraries and frameworks

Aikido Firewall for Python 3 is compatible with:

### Web frameworks

* ✅ [Django](docs/django.md)
* ✅ [Flask](docs/flask.md)

### WSGI servers
* ✅ [Gunicorn](docs/gunicorn.md)
* ✅ [uWSGI](docs/uwsgi.md)

### Database drivers
* ✅ [`mysqlclient`](https://pypi.org/project/mysqlclient/)
* ✅ [`PyMySQL`](https://pypi.org/project/PyMySQL/)
* ✅ [`pymongo`](https://pypi.org/project/pymongo/)

## Reporting to your Aikido Security dashboard

> Aikido Security is a developer-first software security platform. We scan your source code & cloud to show you which vulnerabilities are actually important.

You can use some of Firewalls's features without Aikido, but you will get the most value by reporting your data to Aikido.

You will need an Aikido account and a token to report events to Aikido. If you don't have an account, you can [sign up for free](https://app.aikido.dev/login).

Here's how:
* [Log in to your Aikido account](https://app.aikido.dev/login).
* Go to [Firewall](https://app.aikido.dev/runtime/services).
* Go to apps.
* Click on **Add app**.
* Choose a name for your app.
* Click **Generate token**.
* Copy the token.
* Set the token as an environment variable, `AIKIDO_TOKEN`

## Running in production (blocking) mode

By default, Firewall will only detect and report attacks to Aikido.

To block requests, set the `AIKIDO_BLOCKING` environment variable to `true`.

See [Reporting to Aikido](#reporting-to-your-aikido-security-dashboard) to learn how to send events to Aikido.


## Bug bounty program

Our bug bounty program is public and can be found by all registered Intigriti users at: https://app.intigriti.com/researcher/programs/aikido/aikidoruntime
