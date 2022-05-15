# Managair - The Clair Management Server

Managair is part of the _Clair Platform_[^como-note], a system to collect measurements from networked CO2-sensors for indoor air-quality monitoring. It is developed and run by the [Clair Berlin Initiative](https://clair-berlin.de), a non-profit, open-source initiative to help operators of public spaces lower the risk of SARS-CoV2-transmission amongst their patrons.

Technically speaking, Managair is a service in the [Clair Stack](https://github.com/ClairBerlin/clair-stack), which is the infrastructure-as-code implementation of the Clair Platform.

Managair can also be run as `ingestair`, an application that ingests samples received via an HTTP API. Both the management functionality and the ingest functionality reside in the same code base because they share a common database.

## Functionality

Managair is the key administrative service of the _Clair Stack_. It is a [Django](https://www.djangoproject.com) web application that manages users, their inventory of sensor nodes, and the measurement samples recorded by these nodes.

- The samples that are received and decoded by specific _protocol handlers_ in the Clair Stack, Managair offers an _ingestion_ API endpoint that takes a sample and persists it in the underlying [PostgrSQL](https://www.postgresql.org) database.
- A [RESTful API](doc/api.md) offers resources for CRUD operations on all inventory entities, like nodes, rooms, or sensor installations. This API furthermore provides resources to retrieve time series of measured samples for display and analysis.
- Administrative access to all entities is possible via the [Django Admin-UI](https://docs.djangoproject.com/en/3.1/ref/contrib/admin/).
- Managair enforces an access control policy whereby resources and samples are visible to users that are members of a given _organization_ only, but can be made public explicitly.
- An independent _fidelity service_ checks if data is received regularly from each node.
- Publishers allow to forward samples to other IoT data platforms if the corresponding sensor installation was marked as _public_.

## The Managair Data Model

At the core of the Managair is a multitenant data model. A graph of the implemented entity-relationship model is available [here](/doc/inventory-model.pdf)

- Key entity is the _organization_, which stands for a legal entity like a bar, restaurant, a retail store or a dentist practice. An organization can also stand for large institutions, like a retail chain or a university.
- A _user_ is a digital identity for a natural person. Each user is identified by a username and authenticated via a password.
- A user can be a _member_ of one or more organizations. For each organization, the membership can take on one of two _roles_:
  - A user with the _OWNER_ role has full control over all resources that belong to the organization.
  - The INSPECTOR has read access only.
- An organization owns one or more sensor _nodes_. Each node reports measurement _samples_ over time, where each sample is time-stamped and contains at least a CO2 measurement. Depending on the node _model_ and the node _protocol_, a node might report additional measurement _quantities_.
- Each organization can command one or more _sites_. A site models a physical location with an address and geo-coordinates. Examples for a site might be a restaurant, a pharmacy, a school, or a department store.
- Each site can consist of one or more _rooms_. Each room, in turn, can be characterized by its size, height, and maximum occupancy.
- The organization's sensor nodes are associated with a certain room by means of an _installation_. Each installation is valid for a given duration with start and end date and time. This way, a single node can be subsequently installed at varios locations in one or more rooms.
- All entities listed above are by default _private_. Only authenticated members of the organization can access the resources of the organization via the Managair REST API. However, each installation can be declared _public_. In this case, the room, site, and organization that contains this installation become public as well and can be accessed via the Managair API without prior authentication.
- A _time series_ is a sequence of samples recorded by one node. Time series can be accessed on a per-node basis and on a per-installation basis. A _node-time-series_ covers the entire lifetime of the node, whereas an _installation-time-series_ covers the duration of the installation only. Installation time-series are publicly accessible if the installation itself is marked as public. Node time-series are accessible to the organization only.

## Architecture

Managair is a [Django](https://www.djangoproject.com) web application, written in [Python 3](https://www.python.org). The primary REST API adheres to the [JSON:API](https://jsonapi.org) specification. To implement this API, we use the [Django REST Framework](https://www.django-rest-framework.org) (DRF) and the extension [Django REST Framework JSON API](https://django-rest-framework-json-api.readthedocs.io/en/stable/) (DJA). Authentication is handled by DRF's [session authentication](https://www.django-rest-framework.org/api-guide/authentication/) and as token-based authentication provided by [DJ-Rest-Auth](https://github.com/jazzband/dj-rest-auth). Our task queue for the fidelity check services is provided by [Django-Q](https://django-q.readthedocs.io/en/latest/).

## REST API

Documentation of the Managair ReST API is available

- [as plain text with explanations](/doc/api.md)
- for download as an OpenAPI 3.0 YAML document at `/api/v1/schema`
- as a [Swagger-UI](https://swagger.io/tools/swagger-ui/) web page at `/api/v1/schema/swagger-ui`
- and as a [ReDoc](https://github.com/Redocly/redoc) web page at `/api/v1/schema/redoc`

If you make changes to the API, you need to re-generate the corresponding OpenAPI description file. To do so, execute `python3 manage.py spectacular --file schema.yaml`, or - if you run the _Clair Stack_ atop inside docker swarm: `manage-py.sh <env> spectacular --file schema.yaml`.

The `schema.yaml` should end up in the project's root folder, from where `docker build` will correctly package it.

## Deployment

The Managair is designed to be deployed as part of the _Clair Stack_, a docker swarm setup that comprises the configuration of all services necessary to ingest node data and serve it via the Managair API to frontend applications.

Even though docker swarm automates most deployment tasks for the entire Clair Stack, there are several tasks that pertain to the Managair service proper:

### Static Files

HTML Templates, CSS, and media for the admin-UI and the browsable API are part of the Managair service. In a typical web application, it would be the job of a webserver to serve these files - as described in the [Django documentation](https://docs.djangoproject.com/en/3.1/howto/static-files/deployment/.) To simplify configuration, and to align development with production setups, we take a somewhat different route and use the [White Noise](http://whitenoise.evans.io/en/stable/django.html) module instead. With the White Noise middleware installed, Managair can serve its own static files without the help of an additional webserver. This is not quite as performant but requires much less configuration and fewer manual steps during deployment.

Upon a fresh deployment, or whenever static files have changed, you can force Django to collect all static files from all registered Django apps into a common folder by running `python manage.py collectstatic`. The `entrypoint.sh` script of the Managair docker container automatically performs this task if the environment variable `COLLECT_STATIC_FILES` is set to `true`.

### Translations

For the accounts, templates are used that contain strings which can be translated. This is done for german (`de`). The process was:

- `cd accounts`
- `mkdir locale`
- `django-admin makemessages -l de`
- add translations to `locale/de/LC_MESSAGES/django.po`
- `django-admin compilemessages` to create the `.mo` file which is used for rendering

When changing the templates, run:

- `django-admin makemessages -a`
- update translations in `locale/de/LC_MESSAGES/django.po`
- `django-admin compilemessages`

\_NOTE: the default language is determined in `settings.py` via `LANGUAGE_CODE`.

### Secrets

Managair requires several secrets:

- SECRET_KEY: The standard [Django secret key](https://docs.djangoproject.com/en/3.1/ref/settings/#secret-key) that is used for digital signatures and to derive password salts.
- SQL_PASSWORD: Password to connect to the main database.
- EMAIL_HOST_PASSWORD: Password for the SMTP server used for sending mails.
- SENTRY_URL: When using [Sentry.io](https://sentry.io) as a remote-monitoring service, sentry's ingestion URL is a (weak) secret. Sentry remote monitoring is activated setting the environment variable `SENTRY=True`.

Several more secrets might be necessary for integration with other IoT data platforms. For example, the integration with [Stadtpuls Berlin](https://stadtpuls.com/) (see the section on integrations below) requires the following additional secrets:

- SP_API_KEY
- SP_AUTH_TOKEN
- SP_LOGIN_PWD

Secrets can be passed in either of two ways:

- As value of an environment variable: For each of the secrets listed above, define an environment variable of the same name; e.g., `SECRET_KEY`.
- As file content: Managair reads the secret value from a file where the filename must be provided via an environment variable `<secret_name>_FILE`; e.g., `SECRET_KEY_FILE`. This mechanism can be used in combination with [Docker secrets](https://docs.docker.com/engine/swarm/secrets/#use-secrets-in-compose), where Docker provides secrets to services as files inside an encrypted RAM-disk mounted at `/run/secrets/<secret>` inside the container.

### Environment

The following environment variables are available to influence Managair setup. Shown are their default settings:

- `SECRET_KEY` or `SECRET_KEY_FILE`. Secret as explained above.
- `DEBUG=0`. Set to `1` to use [Django's debug mode](https://docs.djangoproject.com/en/3.1/ref/settings/#std:setting-DEBUG) with hot reload. Never use in production!
- `DEBUG_TOOLBAR=0`. Set to `1` to activate the [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/). Never use in production.
- `SENTRY=0`. Set to `1` to activate remote monitoring via [Sentry.io](https://sentry.io).
- `SENTRY_URL`. Secret ingest URL, as explained above.
- `IOTDP_INTEGRATION=0`. Boolean flag to enable forwarding of ingested samples to other IoT data platforms. Disabled by default. Set to `1` to enable integrations implemented via the mechanism explained in the Integrations section below.
- `NODE_FIDELITY=0`. Set to `1`to activate regular monitoring of node traffic. The status of all nodes can be queried via the [API](./doc/api.md) at `/api/v1/fidelity`.
- `DJANGO_ALLOWED_HOSTS`. Hosts allowed to connect. See the [Django documentation](https://docs.djangoproject.com/en/3.1/ref/settings/#allowed-hosts) for details.
- `EMAIL_HOST`. Host name of the SMTP server used to send emails. See the [Django email engine](https://docs.djangoproject.com/en/3.1/topics/email/) documentation for details.
- `EMAIL_PORT=587`. Port of the SMTP server used to send emails.
- `EMAIL_HOST_USER`. User name to connect to the SMTP server.
- `EMAIL_HOST_PASSWORD` or `EMAIL_HOST_PASSWORD_FILE`. Secret as explained above.
- `EMAIL_USE_TLS=True`.
- `DEFAULT_FROM_EMAIL`. Default Reply-to email address for sent mails.
- `SQL_ENGINE=django.db.backends.sqlite3`. Default SQL database engine. Do not use SQLite in production. Consult the documentation on [Django database backends](https://docs.djangoproject.com/en/3.1/ref/databases/).
- `SQL_DATABASE=db.sqlite3`. Name of the main database to connect to.
- `SQL_USER=user`. Default database user.
- `SQL_PASSWORD` and `SQL_PASSWORD_FILE`. The database user's password, as explained above.
- `SQL_HOST=localhost`. Host name on which the DBMS is running.
- `SQL_PORT=5432`. Port to connect to the DBMS.
- `LOG_LEVEL=INFO`. Log level for the Managair application. Only messages with log level of the given severity or higher will be logged. Must be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. See the [Django logging documentation](https://docs.djangoproject.com/en/3.1/topics/logging/) for details.
- `DJANGO_DB_LOG_LEVEL=WARNING`. Log level for DBMS messages only.
- `DJANGO_LOG_LEVEL=WARNING`. Log level for Django-internal messages.

The following environment variables determine how Managair is launched inside its Docker container, via the `entrypoint.sh` script:

- `DB_MIGRATE=False`. Execute new database migrations upon launch, if available.
- `COLLECT_STATIC_FILES=False`. Collect static files in a central location to be served via [WhiteNoise](http://whitenoise.evans.io/en/stable/).

## User Registration and Authentication

The Managair uses [dj-rest-auth](https://dj-rest-auth.readthedocs.io/en/latest/index.html) for user authentication, in combination with the registration functionality from [django-allauth](https://django-allauth.readthedocs.io/en/latest/index.html). Authentication and registration is available at the `/auth/` endpoint; individual resources follow the [dj-rest-auth documentation](https://dj-rest-auth.readthedocs.io/en/latest/api_endpoints.html).

Like for the operational API, authentication and registration resources must be JSON:API documents with Content-Type `application/vnd.api+json`. For example, the body of a login request must look as follows:

```json
{
  "data": {
    "type": "LoginView",
    "attributes": {
      "username": "maxMustermann",
      "password": "mustermann"
    }
  }
}
```

## Node Status Fidelity Check

The Managair contains a background service that periodically checks for all registered nodes if a message has been received recently, within the last two hours (configurable). If so, Managair marks the node's _fidelity_ as _ALIVE_. If the most recent sample is not older than twice this period (four hours), the node is marked _MISSING_. A node that has been quiet for longer is declared _DEAD_, while a node from which no messages have ever been received is _UNKNOWN_.

The periodic fidelity check is performed by means of the background task scheduler [Django_Q](https://django-q.readthedocs.io/en/latest/index.html). It is active if the environment variable `NODE_FIDELITY` is set (=1).

Once the entire application stack has booted, you currently need to start its job queue by hand, via the command. `python3 manage.py qcluster`; or, on the _Clair Stack_, `manage-py.sh <env> qcluster`.

Then, open up the admin-UI and schedule a Live-Node Check at an interval of your choice. The function to call is `core.tasks.check_node_fidelity`.

Results of the fidelity check are available at the API resource `api/v1/fidelity`, or via the admin UI.

## Integrations

Managair in its sample-ingest configuration provides for a means to forward incoming samples to other IoT data platforms (IOTDP). For each incoming sample, the ingester determines if the sample corresponds to an active _installation_ and if this installation has the flag `is_public` set to `true`. If so, the ingester publishes a [Django signal](https://docs.djangoproject.com/en/4.0/topics/signals/) that can be picked up by a custom integration application for use. In this way, it is possible to develop [Django applications](https://docs.djangoproject.com/en/4.0/ref/applications/) that subscribe to this signal. How each application performs the actual integration may differ.

As a first example, Managair comes with an integration for [Stadtpuls Berlin](https://stadtpuls.com/), implemented as Django application `stadtpuls_integration`. This application has its own data model in the Django DB that stores which installations have already been registered with Stadtpuls. For each signal trigger, the Stadtpuls integration checks if the installation that corresponds to the incoming sample has already been registered with Stadtpuls. If yes, it maps the internal installation ID to the corresponding Stadtpuls sensor ID, converts the sample data format, and forwards it to the Stadtpuls ingest API. If not, it first registers a new Stadpuls sensor and then proceeds as above.

## Development Setup

Managair is a [Django](https://www.djangoproject.com/) web application atop a [PostgreSQL](https://www.postgresql.org) DBMS. It is meant to be run as part of the Clair backend stack. To start up your development environment, consult the stack's Readme-file.

### Debugging

When run in DEBUG mode, the `managair_server` has the [Python Tools for Visual Studio Debug Server](https://github.com/microsoft/ptvsd) (PTVSD) included. It allows to attach a Python debugger from within Visual Studio Code to the application running inside the container. To get started, copy `dev_utils/launch.json` into your project-local `.vscode` folder. To attach the debugger to the _Managair_ application running inside a container, select the _Debug Django_ run-configuration on the VS-Code debug pane. If the status bar turns from blue into orange, the debugger is attached. Set a breakpoint and fire a request to get going. Details on setup and usage can be found in this [blog post](https://testdriven.io/blog/django-debugging-vs-code/).

### Django Debug Toolbar

When the debug mode is activated via the environment variable `DEBUG=1`, the [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/index.html) becomes visible on all HTML views; e.g., the admin UI or the browsable ReST API.

### Data Fixtures

To start development work right away, it would be convenient if important data was preloaded into the DB already. This is what [Django fixtures](https://docs.djangoproject.com/en/3.1/howto/initial-data/) are for. Fixture files are JSON files that contain data in a format that can be directly imported into the DB. They are available for the individual applications in their `fixture` folders. To set up the the application for development, load the fixtures as follows:

- `python3 manage.py loaddata user_manager/fixtures/user-fixtures.json`
- `python3 manage.py loaddata core/fixtures/inventory-fixtures.json`
- `python3 manage.py loaddata core/fixtures/data-fixtures.json`

Make sure to respect the order because of foreign-key constraints. When Managair is executed in a docker container, the above commends must be executed inside the container; e.g., via `docker exec`. If you run _Clair Stack_, which is built atop docker swarm, you can use the `manage-py.sh` shell script to execute your Django management command inside the correct container.

### Tools and Conventions

- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
- Linting and static analysis: [Prospector](http://prospector.landscape.io/en/master/)

## Testing

Django comes with extensive [testing support](https://docs.djangoproject.com/en/3.1/topics/testing/overview/), from unit tests, tests of the DB interaction to full-blown integration tests. As Django installs a separate testing DB, most of the tests could even be run on a production system without interfering with its operation. Therefore, we currently do not have a separate testing configuration of the Clair Stack - simply run the tests on your local development stack.

To execute the tests, use the following Django management command

```shell
$> python3 manage.py test <app>
```

where `<app>` is the Django application for which to execute test cases. For the Managair, it will most likely be `core`. For more detailed control about the tests to run, consult the [testing documentation](https://docs.djangoproject.com/en/3.1/topics/testing/overview/#running-tests).

The tests can be executed perfectly well on a running Clair Stack on docker swarm. Use the management tool as follows:

```shell
$> ./tools/manage-py.sh environments/dev.env test core
```

### Debuggin While Testing

When doing test-driven development, or simply while developing tests, it is quite common that things don't work out as intended. In such a case, it is very helpful to set a breakpoint and launch into a debugging session right where the problem occurs. When running the _Managair_ application as part of the Clair Stack, the debugger must be attached remotely.

Unfortunately, the standard attach procedure outlined above does not work - the debugger there waits for the development server to reload, which does not happen during testing. Instead, there is a separate debug configuration for use in Visual Studio Code: Select the _Debug Django Tests_ run configuration and set a breakpoint in the test case you are working on. Then, use the Python script `debugtests.py` to start a test session with debug support. On docker swarm, execute it via

```shell
docker exec -it $(docker ps -q -f name=managair_server) python3 debugtests.py <test-args>
```

Once the script prompts `Waiting for external debugger...`, switch back to VS-Code and execute the _Debug Django Tests_ run configuration (click on the green arrow).

[^como-note]: The Clair Platform and the Clair-Berlin initiative are now part of the [CO2-Monitoring (COMo) project](https://www.technologiestiftung-berlin.de/projekte/como-berlin), funded by a grant from the [Senate Chancellery of the Governing Mayor of Berlin](https://www.berlin.de/rbmskzl/en/).
