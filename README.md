![Aikido Zen for Python 3](https://raw.githubusercontent.com/AikidoSec/firewall-python/main/docs/banner.svg)

# Zen, in-app firewall for Python 3  | by Aikido
[![Codecov](https://img.shields.io/codecov/c/github/AikidoSec/firewall-python?style=flat-square&token=AJK9LU35GY)](https://app.codecov.io/gh/aikidosec/firewall-python) 
[![PyPI Package](https://img.shields.io/pypi/v/aikido_zen?style=flat-square)](https://pypi.org/project/aikido_zen/)
![Code Style : Black](https://img.shields.io/badge/code%20style-black-black?style=flat-square)
[![Unit tests](https://github.com/AikidoSec/firewall-python/actions/workflows/unit-test.yml/badge.svg)](https://github.com/AikidoSec/firewall-python/actions/workflows/unit-test.yml) 
[![End to end tests](https://github.com/AikidoSec/firewall-python/actions/workflows/end2end.yml/badge.svg)](https://github.com/AikidoSec/firewall-python/actions/workflows/end2end.yml)

Zen, your in-app firewall for peace of mind– at runtime.

Zen is an embedded Web Application Firewall that autonomously protects your Python apps against common and critical attacks.

Zen protects your Python apps by preventing user input containing dangerous strings, which allow SQL injections. It runs on the same server as your Python app for simple [installation](https://pypi.org/project/aikido_zen/#installation) and zero maintenance.

## Features

Zen will autonomously protect your Python applications from the inside against:

* 🛡️ [NoSQL injection attacks](https://www.aikido.dev/blog/web-application-security-vulnerabilities)
* 🛡️ [SQL injection attacks](https://www.aikido.dev/blog/the-state-of-sql-injections)
* 🛡️ [Command injection attacks](https://www.aikido.dev/blog/command-injection-in-2024-unpacked)
* 🛡️ [Path traversal attacks](https://www.aikido.dev/blog/path-traversal-in-2024-the-year-unpacked)
* 🛡️ [Server-side request forgery (SSRF)](./docs/ssrf.md)

Zen operates autonomously on the same server as your Python app to:

* ✅ Secure your app like a classic web application firewall (WAF), but with none of the infrastructure or cost.

## Supported libraries and frameworks

Zen for Python 3 is compatible with:

### Web frameworks

* ✅ [Django](docs/django.md)
* ✅ [Flask](docs/flask.md)
* ✅ [Quart](docs/quart.md)
* ✅ [Starlette](docs/starlette.md)
* ✅ [FastAPI](docs/fastapi.md)


### WSGI servers
* ✅ [Gunicorn](docs/gunicorn.md)
* ✅ [uWSGI](docs/uwsgi.md)

### Database drivers
* ✅ [`mysqlclient`](https://pypi.org/project/mysqlclient/) ^1.5
* ✅ [`PyMySQL`](https://pypi.org/project/PyMySQL/) ^0.9
* ✅ [`pymongo`](https://pypi.org/project/pymongo/) ^3.10
* ✅ [`psycopg2`](https://pypi.org/project/psycopg2) ^2.9.2
* ✅ [`psycopg`](https://pypi.org/project/psycopg) ^3.1
* ✅ [`asyncpg`](https://pypi.org/project/asyncpg) ^0.27
* ✅ [`motor`](https://pypi.org/project/motor/) (See `pymongo` version)

## Reporting to your Aikido Security dashboard

> Aikido is your no nonsense application security platform. One central system that scans your source code & cloud, shows you what vulnerabilities matter, and how to fix them - fast. So you can get back to building.

Zen is a new product by Aikido. Built for developers to level up their security. While Aikido scans, get Zen for always-on protection. 

You can use some of Zen’s features without Aikido, of course. Peace of mind is just a few lines of code away.

But you will get the most value by reporting your data to Aikido.

You will need an Aikido account and a token to report events to Aikido. If you don't have an account, you can [sign up for free](https://app.aikido.dev/login).

Here's how:
* [Log in to your Aikido account](https://app.aikido.dev/login).
* Go to [Zen](https://app.aikido.dev/runtime/services).
* Go to apps.
* Click on **Add app**.
* Choose a name for your app.
* Click **Generate token**.
* Copy the token.
* Set the token as an environment variable, `AIKIDO_TOKEN`

## Running in production (blocking) mode

By default, Zen will only detect and report attacks to Aikido.

To block requests, set the `AIKIDO_BLOCK` environment variable to `true`.

See [Reporting to Aikido](#reporting-to-your-aikido-security-dashboard) to learn how to send events to Aikido.

## Additional configuration

[Configure Zen using environment variables for authentication, mode settings, debugging, and more.](https://help.aikido.dev/doc/configuration-via-env-vars/docrSItUkeR9)

## Benchmarks 
The following table summarizes the performance of both a typical SQL Query and a typical NoSQL Query with and without the Zen, measured in milliseconds :
| Operation | Avg. time w/o Zen | Avg. time w/ Zen | Delta | Delta in % |
| --------- | ---------------------- | --------------------- | ----- | ---------- |
| SQL Query | 1.222 ms | 1.257 ms | +0.035 ms | +3% |
| NoSQL Query | 1.090 ms | 1.110 ms | +0.020 ms | +2% |

See [benchmarks](benchmarks/) folder for more.

## Bug bounty program

Our bug bounty program is public and can be found by all registered Intigriti users [here](https://app.intigriti.com/researcher/programs/aikido/aikidoruntime)

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## Code of Conduct

See [CODE_OF_CONDUCT.md](.github/CODE_OF_CONDUCT.md) for more information.

## Security

See [SECURITY.md](.github/SECURITY.md) for more information.
