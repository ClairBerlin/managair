# Managair - The Clair Management Interface

## Functionality

### User-Facing Services

- Register a new user, update a user's profile [rough sketch available].
- Register a sensor node, remove a sensor node [API and admin-UI].
- Add a location, associate sensor nodes with a location, update location information [rough sketch via API and admin-UI].
- Inspect and measurement time-series [API].
- Analyze measurement time-series and derived data [open].
- GDPR transparency: export personal data, delete an account and all associated data [open].

### Administrative Services

- User management: Register and update users. Change user permissions.
- Device management: Add and update node types [Available via the Django admin UI].
- System administration [Django admin UI]
- Fidelity check for all registered nodes: Warn if no messages have been received lately [adnin UI].

## Deployment

The Managair is desiged to be deployed as part of the _Clair Stack_, a docker swarm setup that comprises the configuration of all services necessary to ingest node data and serve it via the Managair API to frontend applications.

Even though docker swarm automates most deployment tasks for the entire Clair Stack, there are several tasks that pertain to the Managair service proper:

### Static Files

HTML Templates, CSS, and media for the admin-UI and the browsable API are part of the Managair service. In a typicall web application, it would be the job of a webserver to serve these files - as described in the [Django documentation](https://docs.djangoproject.com/en/3.1/howto/static-files/deployment/.) To simplify configuration, and to align development with production setups, we take a somewhat different route and use the [White Noise](http://whitenoise.evans.io/en/stable/django.html) module instead. With the White Noise middleware installed, Managair can serve its own static files without the help of an additional webserver. This is not quite as performant but requires much less configuration and fewer manual steps during deployment.

Upon a fresh deployment, or whenever static files have changed, you can force Django to collect all static files from all registered Django apps into a common folder by running `python manage.py collectstatic`. The `entrypoint.sh` script of the Managair docker container automatically performs this task if the environment variable `COLLECT_STATIC_FILES` is set to `true`.

## Development Setup

Managair is a [Django](https://www.djangoproject.com/) web application atop a [PostgreSQL](https://www.postgresql.org) DBMS. It is meant to be run as part of the Clair backend stack. To start up your development environment, consult the stack's Readme-file.

### Debugging

When run in DEBUG mode, the `managair_server` has the [Python Tools for Visual Studio Debug Server](https://github.com/microsoft/ptvsd) (PTVSD) included. It allows to attach a Python debugger from within Visual Studio Code to the application running inside to container. To get started, copy `dev_utils/launch.json` into your project-local `.vscode` folder. Details on setup and usage can be found in this [blog post](https://testdriven.io/blog/django-debugging-vs-code/).

### Django Debug Toolbar

When the debug mode is activated via the environment variable `DEBUG=1`, the [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/index.html) becomes visible on all HTML views; e.g., the admin UI or the browsable ReST API.

### Data fixtures

To start development work right away, it would be convenient if important data was preloaded into the DB already. This is what [Django fixtures](https://docs.djangoproject.com/en/3.1/howto/initial-data/) are for. Fixture files are JSON files that contain data in a format that can be directly importet into the DB. They are available for the individual applications in their `fixture` folders. To set up the the application for development, load the fixtures as follows:

- `python3 manage.py loaddata user_manager/fixtures/user-fixtures.json`
- `python3 manage.py loaddata core/fixtures/inventory-fixtures.json`
- `python3 manage.py loaddata core/fixtures/data-fixtures.json`

Make sure to respect the order because of foreign-key constraints. When Managair is executed in a docker container, the above commends must be executed inside the container; e.g., via `docker exec`. If you run _Clair Stack_, which is built atop docker swarm, you can use the `manage-py.sh` shell script to execute your Django management command inside the correct container.

### Tools and Conventions

- [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
- Linting: [PyLint](https://www.pylint.org)

## OpenAPI Schema

Documentation of the Managair ReST API is available

- for download as an OpenAPI 3.0 YAML document at `/api/v1/schema`
- as a [Swagger-UI](https://swagger.io/tools/swagger-ui/) web page at `/api/v1/schema/swagger-ui`
- and as a [ReDoc](https://github.com/Redocly/redoc) web page at `/api/v1/schema/redoc`

If you make changes to the API, you need to re-generate the corresponding OpenAPI description file. To do so, execute `python3 manage.py spectacular --file schema.yaml`, or - if you run the _Clair Stack_ atop inside docker swarm: `manage-py.sh <env> spectacular --file schema.yaml`.

The `schema.yaml` should end up in the project's root folder, from where `docker build` will correctly package it.

## User Registration and Authentication

The Managair uses [dj-rest-auth](https://dj-rest-auth.readthedocs.io/en/latest/index.html) for user authentication, in combination with the registration functionality from [django-alauth](https://django-allauth.readthedocs.io/en/latest/index.html). Authentication and registration is available at the `/auth/` endpoint; individual resources follow the [dj-rest-auth documentation](https://dj-rest-auth.readthedocs.io/en/latest/api_endpoints.html).

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

## Testing

Dajngo comes with extensive [testing support](https://docs.djangoproject.com/en/3.1/topics/testing/overview/), from unit tests, tests of the DB interaction to full-blown integration tests. As Django installs a separate testing DB, most of the tests could even be run on a production system without interfering with its operation. Therefore, we currently do not have a separate testing configuration of the Clair Stack - simply run the tests on your local development stack.

To execute the tests, use the following Django management command

```shell
$> python3 manage.py test <app>
```

where `<app>` is the Django application for which to execute test cases. For the Managair, it will most likely be `core`. For more detailed control about the tests to run, consult the [testing documentation](https://docs.djangoproject.com/en/3.1/topics/testing/overview/#running-tests).

The tests can be executed perfectly well on a running Clair Stack on docker swarm. Use the management tool as follows:

```shell
$> ./tools/manage-py.sh environments/dev.env test core
```
