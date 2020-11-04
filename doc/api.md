# The Managair REST API

This is a first draft of Managair's API endpoints. It's a design document that describes the intended API endpoints. It does not describe the API as it is currently implemented.

## API Root and API Structure

Root: `/api/v1/`

Main API branches:

- **User:** Registration, authentication, and user profiles.
- **Inventory:** Resources from the perspective of a specific organization - all their sites, rooms, nodes, and data reported by these nodes. Requires login.
- **Public:** Publicly available information on sites and corresponding time series.

All collection-resources support paging. HTTP verbs follow the [standardized semantics](https://blog.eq8.eu/article/put-vs-patch.html). See also [here](https://williamdurand.fr/2014/02/14/please-do-not-patch-like-an-idiot/#disqus_thread) and [here](https://stackoverflow.com/questions/28459418/use-of-put-vs-patch-methods-in-rest-api-real-life-scenarios/39338329#39338329)

## User

Most of the user-management endpoints are provided by the [dj-rest-auth library](https://dj-rest-auth.readthedocs.io/en/latest/api_endpoints.html). The user must be logged in to access most of the resources, except to register and to log-in.

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

## Inventory

The inventory is organized according to organizations that have one or more rooms with installed sensor nodes. All inventory resources require the user to be logged in. Data is organizaed according to the nodes that reported them. Data resources for a given organization are available only for the time-period when the node is or was owned by the organization.

### Organizations

- `/api/v1/organizations/` Collection-resource of all organizations visible to the logged-in user.
  - [GET] List the organizations.
  - [POST] Register a new organization, with the logged-in user as owner.
- `/api/v1/organizations/<organization_id>/` Details-resource of the organization with ID `organization_id`.
  - [GET] Details about the organization. Only available if the logged-in user is a member of this organization.
  - [PUT, PATCH] Replace resp. update organization data. Only available for users that have the OWNER role for the organization.
  - [DELETE] Remove the organization and all assets and data it owns - sites, rooms, nodes, and node time series. Only available for users that have the OWNER role for the organization.
- `/api/v1/organizations/<organization_id>/relationships/users/` Relationship resource to manage the users that form part of the organization. See the [JSON:API specification](https://jsonapi.org/format/#crud-updating-to-many-relationships) for detailed semantics.
  - [GET] List the user-members of the organization.
  - [POST] Add one or more existing users as members of the organization. The default membership role will be _INSPECTOR_, which is the least-privileged role (read-only.)
  - [DELETE] Delete the member specified in the request body. **WARNING** Allows the logged-in user to be removed from the organization.
- `/api/v1/organizations/<organization_id>/users/` Collection-resource for the organizations members; that is, the users that are part of the organization.
  - [GET] List the members, with individual links to the membership detail resouces at `/api/v1/users/<user_id>/`.
- `/api/v1/organizations/<organization_id>/relationships/nodes/` Relationship resource to manage the nodes owned by the organization.
  - [GET] List the nodes owned by the organization.
  - [POST]
  - [PATCH]
  - [DELETE]
- `/api/v1/organizations/<organization_id>/nodes/` Collection-resource of all nodes that belong to the specified organization.
  - [GET] List all nodes owned by the organization, with individual links to node detail resources at `/api/v1/nodes/<node_id>`.
  - [POST] Register a new node that is currently unknown to the Managair. This new node will be attributed to the goven organization.
- `/api/v1/organizations/<organization_id>/sites/` Collection-resource of all sites that belong to the organization `organization_id`.
  - [GET] List the sites, with individual links to the detail-resource at `/api/v1/sites/<site_id>`.

### Users

- `/api/v1/users/` Collection resource of all users visible to the logged-in user.
  - [GET] List the users. Filter to see members of one specific organization via the filter `filter[organization]=<organization_id>`.
- `/api/v1/users/<user_id>/` Detail resource for a user's membership in the organization.
  - [GET] Retrieve membership details. The membership contains the user's role and relations, and a nested `/api/v1/auth/user/<user_id>` resource.
  - [PUT, PATCH] Replace resp. update membership details. The logged-in user must be an OWNER of the organization to perform this task.
  - [DELETE] Revoke membership of a user. This action does not delete the user account, only the organization membership is affected. The logged-in user must be an OWNER of the organization to perform this task.
- `/api/v1/users/<user_id>/relationships/organizations/` Relationship resource to manage the organizations a user is part of. This resource is the counterpart to `/api/v1/organizations/<organization_id>/relationships/users/`.
  - [GET] List the organizations the user is part of.
  - [POST]
  - [PATCH]
  - [DELETE]
- `/api/v1/users/<user_id>/organizations/` Collection-resource of all organizations that the user is a member of.
  - [GET] List all organizations of which the given user is a member, with individual links to organization detail resources at `/api/v1/organizations/<organization_id>/`.
  - [POST] Register a new organization membership for the currently logged-in user.

### Nodes

- `/api/v1/nodes/` Collection-resource of the nodes visible to the logged-in user.
  - [GET] List the nodes. Filter to see nodes of one specific organization only via the filter `filter[organization]=<organization_id>`.
- `/api/v1/nodes/<node_id>/` Details-resource of the specified node. Only accessible if the node is visible to the logged-in user.
  - [GET] Retrieve information about the node. Might include fidelity information.
  - [PUT, PATCH] Update node master data; e.g., node alias or tags (feature request).
  - [DELETE] Remove the node and all samples reported by this node.
- `/api/v1/nodes/<node_id>/samples/` Collection-resource of the measurement samples reported by the given node.
  - [GET] Retrieve a list of samples of the given node. Can be paginated. The time-range can be limited via query paramters:
    - `filter[from]` Start timestamp as Unix epoch. Defaults to `0`; i.e.,1970-01-01T00:00:00Z, if not provided.
    - `filter[to]` End timestamp as Unix epoch. Defaults to the current system time `now()`.
- `/api/v1/nodes/<node_id>/timeseries/` Detail resource for the time-series reported by the specified node.
  - [GET] Returns the time series reported by the given node. **Question: How to restrict the time slice to match the attribution between node and organization?** Identical to the resource at `/api/v1/timeseries/<node_id>/`. Supports querying for time slices:
    - `filter[from]`: Start timestamp as Unix epoch. Defaults to `0`; i.e., 1970-01-01T00:00:00Z.
    - `filter[to]`: End timestamp as Unix epoch. Defaults to the current system time `now()`.
- `/api/v1/nodes/<node_id>/relationships/installations/` Relationship resource to manage the attribution of a node to a room over time. This resource is the counterpart to `/api/v1/rooms/<room_id>/relationships/installations/`.
  - [GET] List the installations of the given node over time.
  - [POST]
  - [PATCH]
  - [DELETE]
- `/api/v1/nodes/<node_id>/installations/` Collection-resource of all installations a node has ever undergone.
  - [GET] List all present and past installations of the given node, with individual links to installation detail resources at `/api/v1/installations/<installation_id>/`.
  - [POST] Register a new node installation.
- `/api/v1/nodes/fidelity/` Status list ("fidelity") for all nodes visible to the logged-in user.
  - [GET] The status is updated periodically and indicates if a given node regularly transmits data. Filter to see nodes of one specific organization only via the filter `filter[organization]=<organization_id>`; filter for nodes of a given site via `filter[site]=<site_id>`, and in a given room via `filter[room]=<room_id>`. In the future, additional information might be added, like battery status or error reports.

### Time Series

- `/api/v1/timeseries/` List resource that provides an timeseries overview.
  - [GET] Return a list summary for the timeseries reported by all nodes to which the logged-in user has access. The summary counts the number of samples and provides information on the time span of each time series.
- `/api/v1/timeseries/<node_id>/` Detail resource of the timeseries of node `node_id`
  - [GET] Retrieve the time series of the specified node. This resource is identical to the resource provided at `/api/v1/nodes/<node_id>/timeseries/`. Only available if the node is visible to the logged-in user. Supports querying for time slices:
    - `filter[from]`: Start timestamp as Unix epoch. Defaults to `0`; i.e., 1970-01-01T00:00:00Z.
    - `filter[to]`: End timestamp as Unix epoch. Defaults to the current system time `now()`.

### Sites

- `/api/v1/sites/` Collection-resource of all sites visible to a logged-in user.
  - [GET] List the sites. Filter to see sites of one specific organization only via the filter `filter[organization]=<organization_id>`.
- `/api/v1/sites/<site_id>/` Details-resource of the specified site.
  - [GET] Rertieve the site resource.
  - [PUT, PATCH] Replace resp. update site master data.
  - [DELETE] Remove the site and all rooms within the site. Does not delete nodes attributed to the site or any of its rooms.
- `/api/v1/sites/<site_id>/relationships/rooms/` Relationship resource to manage the rooms that belong to the site.
  - [GET] List the rooms that belong to the given site.
  - [POST]
  - [PATCH]
  - [DELETE]
- `/api/v1/sites/<site_id>/rooms/` Collection-resource of all rooms of the given site.
  - [GET] List the rooms, with individual links to the detail-resource at `/api/v1/rooms/<room_id>`.
  - [POST] Create a new room that is part of the given site.

### Rooms

- `/api/v1/rooms/` Collection-resource of all rooms visible to a logged-in user.
  - [GET] List the rooms. Filter to see sites of one specific organization only via the filter `filter[organization]=<organization_id>`, and the rooms within one specific site via the filter `filter[site]=<site_id>`.
- `/api/v1/rooms/<room_id>/` Details-resource of the specified room.
  - [GET] Retrieve the room resource.
  - [PUT, PATCH] Replace resp. update the room resouce.
  - [DELETE] Remove the room resource and the node-installation it might contain. Does not delete the node resources themselves.
- `/api/v1/rooms/<room_id>/relationships/installations/` Relationship resource to manage the nodes that are installed in the room.
  - [GET] List the nodes installed in the given room.
  - [POST]
  - [PATCH]
  - [DELETE]
- `/api/v1/rooms/<room_id>/installations/` Collection-resource of all node installations in the given room.
  - [GET] List current and past installations, with individual links to the detail-resource at `/api/v1/installations/<installation_id>`.
  - [POST] Associates an already registered node with the room. A node to be associated with a room must not be associated with another room for an overlapping time period.

### Node-Installations

- `/api/v1/installations/` Collection-resource for the all node installation visible to the logged-in user.
  - [GET] List the installations. Filter to see onstallations of one specific organization with the filter `filter[organization]=<organization_id>`, for one specific site with the filter `filter[site]=<site_id>`, for one specific room via the filter `filter[room]=<room_id>`, and for all installations of a specific node via the filter `filter[node]=<node_id>`.
- `/api/v1/installations/<installation_id>/` Details-resource for the installation of the identified node.
  - [GET] Provide details about the installation - time slice, photo, and additional installation information.
  - [PUT, POST] Replace resp. updates the association with the room. To end the association with a room, update it with an end date; this preserves the association history.
  - [DELETE] Removes the association with the room. This removes the association history, as if the node was never associated with the room.

## Public

Public resources are, well, accessible by the general public without prior login. Public resources are a subset of inventory and data resources listed above, where the resource owner has explicitly marked the resource as publicly available.

<!-- TODO -->

## Resources That Are Not Exposed

We currently do not expose the technical resources for

- Node protocols: Details on capabilities of specific protocols, the reporting format and the quantities that can be reported.
- Node models: Details on specific sensor types, like the manufacturer, the actual senor module used, the quantities measured, etc.

## Versioning

<!-- TODO -->