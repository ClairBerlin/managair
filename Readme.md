# Managair - The Clair Management Interface

## Functionality

### User-Facing Services

- Register a new user, update a user's profile [rough sketch available].
- Register a sensor node, remove a sensor node [open].
- Add a location, associate sensor nodes with a location, update location information [open].
- Inspect and analyze measurement time-series and derived data [open].
- GDPR transparency: export personal data, delete an account and all associated data [open].

### Administrative Services

- User management: Register and update users. Change user permissions.
- Device management: Add and update node types [Available via the Django admin UI].
- System administration [Django admin UI]

## Development Setup

Managair is a [Django](https://www.djangoproject.com/) web application atop a [PostgreSQL](https://www.postgresql.org) DBMS. It is meant to be run as part of the Clair backend stack. To start up your development environment, consult the stack's Readme-file.

### Debugging

When run in DEBUG mode, the `managair_server` has the [Python Tools for Visual Studio Debug Server](https://github.com/microsoft/ptvsd) (PTVSD) included. It allows to attach a Python debugger from within Visual Studio Code to the application running inside to container. To get started, copy `dev_utils/launch.json` into your project-local `.vscode` folder. Details on setup and usage can be found in this [blog post](https://testdriven.io/blog/django-debugging-vs-code/).

### Data fixtures

To start development work right away, it would be convenient if important data was preloaded into the DB already. This is what [Django fixtures](https://docs.djangoproject.com/en/3.1/howto/initial-data/) are for. Fixture files are JSON files that contain data in a format that can be directly importet into the DB. They are available for the individual applications in their `fixture` folders. To set up the the application for development, load the fixtures as follows:

- `docker exec -it managair_server python3 manage.py loaddata user_manager/fixtures/user-fixtures.json`
- `docker exec -it managair_server python3 manage.py loaddata core/fixtures/device-fixtures.json`
- `docker exec -it managair_server python3 manage.py loaddata core/fixtures/site-fixtures.json`
- `docker exec -it managair_server python3 manage.py loaddata core/fixtures/data-fixtures.json`

Make sure to respect the order because of foreign-key constraints.

## OpenAPI Schema

Documentation of the Managair ReST API is available

- for download as an OpenAPI 3.0 YAML document at `/api/v1/schema`
- as a [Swagger-UI](https://swagger.io/tools/swagger-ui/) web page at `/api/v1/schema/swagger-ui`
- and as a [ReDoc](https://github.com/Redocly/redoc) web page at `/api/v1/schema/redoc`

If you make changes to the API, you need to re-generate the corresponding OpenAPI description file. To do so, execute `python3 manage.py spectacular --file schema.yaml`, or - if you run the docer development stack inside docker swarm: 

`docker exec $(docker ps -q -f name=managair_server) python3 manage.py spectacular --file schema.yaml`

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
