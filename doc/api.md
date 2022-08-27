# The Managair REST API

This document describes the Managair's external REST API. It provides access to all essential resources for use by external clients such as Single-Page Web Applications (SPAs), native mobile clients, as well as _Clair Widgets_ that can be embedded in other websites.

To simplify client development, the REST API follows the [JSON:API](https://jsonapi.org) specification. We recommend to use an appropriate JSON:API client library.

## API Root and API Structure

Root: `/api/v1/`

In general, the API has a flat structure, where each resource has its own designated API endpoint, like `/api/v1/organizations/` or `/api/v1/nodes/`. Resources are listed as a _collection_, and can be accessed individually as _detail resource_. All collection-resources support paging. HTTP verbs follow [standardized semantics](https://blog.eq8.eu/article/put-vs-patch.html). See also [here](https://williamdurand.fr/2014/02/14/please-do-not-patch-like-an-idiot/#disqus_thread) and [here](https://stackoverflow.com/questions/28459418/use-of-put-vs-patch-methods-in-rest-api-real-life-scenarios/39338329#39338329).

According to the JSON:API specification, related resources are hyperlinked. We recommend clients to follow the links instead of manually parsing and synthesizing resource paths. The most likely entrypoint for a client oriented at operators of public spaces is the Organization resource at `/api/v1/organization/<organization_id>`, while widgets and apps for the general public would probably start at the list of publicly accessible _Sites_ at `/api/v1/sites/`.

## User Management

Most of the user-management endpoints are provided by the [dj-rest-auth library](https://dj-rest-auth.readthedocs.io/en/latest/api_endpoints.html). The user must be authenticated to access most of the resources, except to register and to log-in.

- `/api/v1/auth/login/` [POST]
- `/api/v1/auth/logout/` [POST]
- `/api/v1/auth/password/reset/` [POST]
- `/api/v1/auth/password/reset/confirm/` [POST]
- `/api/v1/auth/password/change/` [POST]
- `/api/v1/auth/user/` [GET, PUT, PATCH] Information on a specific user and updates of user master data.
- `/api/v1/auth/token/confirm/` [POST]
- `/api/v1/auth/token/refresh/` [POST]
- `/api/v1/registration/` [POST]
- `/api/v1/registration/verify-email` [POST]

## Authentication

TODO

## Inventory

The inventory is organized according to organizations that have one or more rooms with installed sensor nodes. For modifications, all inventory resources require the user to be authenticated.

For most resources, there exists at least on API test. Refer to these test cases for examples on how to use the resource.

### Organizations

- `/api/v1/organizations/` Collection-resource of all organizations visible to the authenticated user.
  - [GET] List the organizations.
  - [POST] Register a new organization. The authenticated user will be added as a member of the organization with role OWNER.
- `/api/v1/organizations/<organization_id>/` Details-resource of the organization with ID `organization_id`.
  - [GET] Details about the organization. Only available if the authenticated user is a member of this organization.
  - [PUT, PATCH] Replace resp. update organization data. Only available for users that have the OWNER role for the organization.
  - [DELETE] Remove the organization and all assets and data it owns - sites, rooms, nodes, and node time-series. Only available for users that have the OWNER role for the organization.
- `/api/v1/organizations/<organization_id>/relationships/users/` Relationship resource to manage the users that form part of the organization. See the [JSON:API specification](https://jsonapi.org/format/#crud-updating-to-many-relationships) for detailed semantics.
  - [GET] List the user-members of the organization.
  - [POST] Add one or more existing users as members of the organization. The default membership role will be _INSPECTOR_, which is the least-privileged role (read-only).
  - [DELETE] Delete the membership specified in the request body. This will not delete the user, jsut the membership. **WARNING** Allows the authenticated user to be removed from the organization, which might result in an organization without a single OWNER.
- `/api/v1/organizations/<organization_id>/users/` Collection-resource for the organization's members; that is, the users that are part of the organization.
  - [GET] List the users of the organization, with individual links to the user detail resouces at `/api/v1/users/<user_id>/`.
- `/api/v1/organizations/<organization_id>/memberships/` Collection-resource for the organization's memberships.
  - [GET] List the memberships of the organization, with individual links to membership detail resouces at `/api/v1/memberships/<membership_id>/`.
- `/api/v1/organizations/<organization_id>/nodes/` Collection-resource of all nodes that belong to the specified organization.
  - [GET] List all nodes owned by the organization, with individual links to node detail resources at `/api/v1/nodes/<node_id>`.
- `/api/v1/organizations/<organization_id>/sites/` Collection-resource of all sites that belong to the organization `organization_id`.
  - [GET] List the sites, with individual links to the detail-resource at `/api/v1/sites/<site_id>`.

### Users and Organization Membership

- `/api/v1/users/` Collection resource of all users visible to the authenticated user.
  - [GET] List all usernames. Filter to limit the collection:
    - Text-search for a specific user by username or email via tha filter `filter[search]=<search-text>`.
    - See members of one specific organization via the filter `filter[organization]=<organization_id>`.
- `/api/v1/users/<user_id>/` Detail resource for a user. Only those users are accessible that are members of an organization where the authenticated user is also a member of.
  - [GET] Retrieve membership details. The membership contains the user's role and relations, and a nested `/api/v1/auth/user/<user_id>` resource.
- `/api/v1/users/<user_id>/organizations/` Collection-resource of all organizations that the user is a member of.
  - [GET] List all organizations of which the given user is a member, with individual links to organization detail resources at `/api/v1/organizations/<organization_id>/`.
- `/api/v1/users/<user_id>/memberships/` Collection-resource of all organization-memberships that the user holds. This resource is very similar to `/api/v1/users/<user_id>/organizations/`. However, it does not directly link to the organization the memberhsip pertains to, but includes the membership role instead.
  - [GET] List all memberships the given user holds, with individual links to membership detail resources at `/api/v1/memberships/<membership_id>/`.
- `/api/v1/memberships/` Collection resource of all memberships visible to the currently authenticated user; i.e., memberships for all organizations where the currently authenticated user is itself a member.
  - [GET] List all memberships visible to the currently authenticated user. Narrow-down the result via the following filters:
    - `filter[organization]=<organization_id>`: Return memberships of the given organization only.
    - `filter[username]=<username>` or `filter[user]=<user_id>`: Return memberships of the given user only. Note that only memberships in organizations will be returned of which the currently authenticated user is also a member.
  - [POST] Register a new member of an organization for which the authenticated user must be an OWNER.
- `/api/v1/memberships/<membership_id>/` Details-resource of the specified membership. Only accessible if the authenticated user is also a member of the membership organization.
  - [GET] Retrieve information about the membership.
  - [PUT, PATCH] Update membership: Use to alter membership role.
  - [DELETE] Cancel the membership. Neither user nor organization are affected.
- `/api/v1/memberships/<membership_id>/user` Details-resource of the user-member.
  - [GET] Retrieve the related user resource. This is the same resource as available at `/api/v1/users/<user_id/>`.
- `/api/v1/memberships/<membership_id>/organization` Details-resource of the membership organization.
  - [GET] Retrieve the related organization resource. This is the same resource as available at `/api/v1/organizations/<organization_id/>`.

### Nodes

- `/api/v1/nodes/` Collection-resource of the nodes visible to the authenticated user.
  - [GET] List the nodes. Filter to narrow down the list:
    - Get nodes of one specific organization only via the filter `filter[organization]=<organization_id>`.
    - Search for nodes with a specific alias or device-EUI via the filter `filter[search]=<search-text>`.
    - [POST] Register a new node with an organization for which the authenticated user must be an OWNER.
- `/api/v1/nodes/<node_id>/` Details-resource of the specified node. Only accessible if the node is visible to the authenticated user.
  - [GET] Retrieve information about the node. Always includes the most recent sample reported by the node. Might include fidelity information. By default, the node resource does not return its associated time series. To query for the node's time series, use the following query-parameters:
    - `include_timeseries=True` prompts the _Managair_ to add a `timeseries` list to the attributes of the Node resource.
    - `filter[to]`: End timestamp of the retrieved time series as Unix epoch. Defaults to the current system time `now()`.
    - `filter[from]`: Start timestamp of the retrieved time series as Unix epoch. Defaults to `0`; i.e., 1970-01-01T00:00:00Z.
  - [PUT, PATCH] Update node master data; e.g., node alias.
  - [DELETE] Remove the node and all samples reported by this node.
- `/api/v1/nodes/<node_id>/installations/` Collection-resource of all installations a node has ever undergone.
  - [GET] List all present and past installations of the given node, with individual links to related installation detail resources at `/api/v1/installations/<installation_id>/`.
- `/api/v1/nodes/fidelity/` Status list ("fidelity") for all nodes visible to the authenticated user.
  - [GET] Node fidelity is periodically updated. It indicates if a given node regularly transmits data.
    - Filter to see nodes of one specific organization only via the filter `filter[organization]=<organization_id>`.
    - Filter for nodes of a given site via `filter[site]=<site_id>`.
    - Filter for node in a given room via `filter[room]=<room_id>`.
    - In the future, additional information might be added, like battery status or error reports.

### Sites

- `/api/v1/sites/` Collection-resource of all sites visible to a authenticated user.
  - [GET] List the sites. Filter to narrow down the list:
    - Get sites of one specific organization only via the filter `filter[organization]=<organization_id>`.
    - Search for sites with a specific name or description via the filter `filter[search]=<search-text>`.
- `/api/v1/sites/<site_id>/` Details-resource of the specified site.
  - [GET] Rertieve the site resource.
  - [PUT, PATCH] Replace resp. update site master data.
  - [DELETE] Remove the site and all rooms within the site. Does not delete nodes attributed to the enclosing organization.
- `/api/v1/sites/<site_id>/rooms/` Collection-resource of all rooms of the given site.
  - [GET] List the rooms, with individual links to the related detail-resource at `/api/v1/rooms/<room_id>`.

### Rooms and Node-Installations

- `/api/v1/rooms/` Collection-resource of all rooms visible to a authenticated user.
  - [GET] List the rooms. Filter to narrow down the list:
    - See rooms of one specific organization only via the filter `filter[organization]=<organization_id>`.
    - See the rooms within one specific site only via the filter `filter[site]=<site_id>`.
    - Search for rooms with a specific name or description via the filter `filter[search]=<search-text>`.
- `/api/v1/rooms/<room_id>/` Details-resource of the specified room.
  - [GET] Retrieve the room resource.
  - [PUT, PATCH] Replace resp. update the room resouce.
  - [DELETE] Remove the room resource and the node-installation it might contain. Does not delete the node resources themselves.
- `/api/v1/rooms/<room_id>/installations/` Collection-resource of all node installations in the given room.
  - [GET] List current and past installations, with individual links to the related detail-resource at `/api/v1/installations/<installation_id>`.
- `/api/v1/installations/` Collection-resource for all the node-installation visible to the authenticated user.
  - [GET] List the installations. Filter to narrow down the list:
    - See installations of one specific organization with the filter `filter[organization]=<organization_id>`.
    - See installations of one specific site with the filter `filter[site]=<site_id>`.
    - See installations in one specific room via the filter `filter[room]=<room_id>`.
    - See installations of a specific node via the filter `filter[node]=<node_id>`.
  - [POST] Associate an already-registered node with an already-registered room. A node to be associated with a room must not be associated with another room for an overlapping time period, and the node must belong to the organization that owns the room, too.
- `/api/v1/installations/<installation_id>/` Details-resource for the installation of the identified node.
  - [GET] Provide details about the installation. Always includes the most recent sample reported from the installation. By default, the installation resource does not return its associated time series. To query for the installation time-series, use the following query-parameters:
    - `include_timeseries=True` prompts the _Managair_ to add a `timeseries` list to the attributes of the installation resource. The time series of an installation consists of those samples reported by the installed node over the duration of the installation. If the node is subsequently moved to another installation, the thus resulting samples become part of this other installation time series.
    - `filter[from]`: Start timestamp of the retrieved time series as Unix epoch. Defaults to `0`; i.e., 1970-01-01T00:00:00Z.
    - `filter[to]`: End timestamp of the retrieved time series as Unix epoch. Defaults to the current system time `now()`. If this filter is applied, the latest sample returned is the latest sample within the filtered range.
  - [PUT, PATCH] Replace resp. update the association with the room. To end the association with a room, update it with an end timestamp earlier than 2147483647 (2038-01-19T03:14:07Z); this preserves the association history.
  - [DELETE] Removes the association with the room. This removes the association history, as if the node has never been associated with the room.
- `/api/v1/installations/<installation_id>/image/` Endpoint to upload an image that depicts the installation. The installation detail resource must already exist before addind an image. _Note:_ This is not a REST-like resource.
  - [PUT] Upload an [image file](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) as a multipart content with a single entry named `image`.
- `/api/v1/installations/<installation_id>/room/` Detail-resource of the room the given installation pertains to.
  - [GET] Details of the room, with link to the related room resource at `/api/v1/rooms/<room_id>`.
- `/api/v1/installations/<installation_id>/node/` Detail-resource of the node the given installation pertains to.
  - [GET] Details of the node, with link to the related node resource at `/api/v1/nodes/<node_id>`.

## Data

Measurement data is what the Clair network is all about. Therefore, the API endpoints described next provide access to the most essential resources of the system: samples and time series. A _sample_ is a measurement of one or more _measurement quantities_ taken by one specific node at one specific instant in time. A _time series_ is a chronologically ordered list of samples recorded by a given node.

Time series consist of samples; yet, samples are not resources in their own right, because they always need context: the node that reported them, or the installation where the sample was taken. Therefore, the preferred way to retrieve a time series is as part of the context resource, as already documented.

- A _node time series_ is the entire list of samples ever recorded by the given node, ordered chronologically. Retrieve a node time series via the node resource at `/api/v1/nodes/<node_id>`, and set the query parameter `include-timeseries=True`. Node timeseries are accessible only for authenticated users that are members of the organization owning the node.
- An _installation time series_ is the list of samples taken while a given node was installed at a particular location in a given room. That is, the installation time-series is limited in time by the installation's start and end timestamps. Retrieve an installaton time-series via the installation resource at `/api/v1/installations/<installation_id>/`,and set the query parameter `include-timeseries=True`. Installation time series are publicly accessible if the installation itself is marked as public.

### Data Analysis

In addition to raw measurement data, _Managair_ application can perform certain analysis tasks to return the results only. Currently, we provide two types of _air quality information_ for a given room:

- A monthly _air quality indicator_: In retrospect, this indicator says if a given room had sufficiently good air quality during the given month.
- A histogram the weighted excess CO2-concentration over time for all days of the week in a given month. This histogram says at which days and hours air quality exceeded the threshold of 1000 PPM.

Both analyses are available at the following resource:
`/api/v1/rooms/<room_id>/airquality/<year_month>` The month of interest must be provided in the form `yyyy-mm`.

By default, only the air quality indication, also called _clean air medal_ is returned as a simple boolean value, where `true` indicates good air quality during the month.

Adding the query parameter `?include_histogram=True` triggers computation of the histogram of excess-CO2-scores. This histogram indicates for each day of the week a score how long the CO2-concentration was above the _clean-air-threshold_ of 1000PPM in a given hour. The 24 values per day correspond to 24 hours, from (0:00 - 0:59) up to (23:00 - 23:59).

## Public Resources

By default, all resources described above are private by default. This means that a user must be authenticated to access them. In addition, access to most resources is limited to members of the organization that own the resource. Because a user may be a member of multiple organizations, resouerces of all organizations the user is a member of may be returned in one response.

Public resources are, well, accessible by the general public without authentication. There are no separate public endpoints; public resources are a subset of inventory and data resources listed above. The only entity that can be explicitly marked public are node installations. Once an installation is public, the entire chain _installation-room-site-organization_ becomes public as well. Most importantly, the installation time-series associated with a particular installation is public if and only if the installation is marked as public.

## Resources That Are Not Exposed

We currently do not expose the technical resources for

- Node protocols: Details on capabilities of specific protocols, the reporting format and the quantities that can be reported.
- Node models: Details on specific sensor types, like the manufacturer, the actual senor module used, the quantities measured, etc.

<!-- ## Versioning -->
<!-- TODO -->