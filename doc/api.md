# The Managair REST API

This is a first draft of Managair's API endpoints. It's a design document that describesthe intended API endpoints. It does not describe the API as it is currently implemented.

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

The inventory is organized according to organizations that have one or more rooms with installed sensor nodes. All inventory resources require the user to be logged in. Data is organizaed according to the nodes that reported them. Data resources for a given organization are available only for the time-period when the node was owned by the organization.

- `/api/v1/organizations/` Collection-resource for all organizations.
  - [GET] Users do see only those organizations, including all sub-resources, of which they are a member.
  - [POST] Register a new organization with the logged-in user as owner.
- `/api/v1/organizations/<organization_id>/` Details-resource of the organization with ID `organization_id`.
  - [GET] Only available if the logged-in user is a member of this organization.
  - [PUT, PATCH] Replace resp. update organization data.
  - [DELETE] Remove the organization and all assets and data it owns - sites, rooms, nodes, and node time series.
- `/api/v1/organizations/<organization_id>/members/` Collection-resource for the organizations members; that is, the users that are part of the organization.
  - [GET] List the members.
  - [POST] Add an already existing user to the organization in one of the available roles. The logged-in user must be an OWNER of the organization to perform this task.
- `/api/v1/organizations/<organization_id>/members/<user_id>` Detail resource for a user's membership in the organization.
  - [GET] Retrieve user details. Redirects to `/api/v1/auth/user/`.
  - [PUT, PATCH] Replace resp. update membership details. The logged-in user must be an OWNER of the organization to perform this task.
  - [DELETE] Revoke membership of a user. This action does not delete the user account, only the organization membership is affected. The logged-in user must be an OWNER of the organization to perform this task.
- `/api/v1/organizations/<organization_id>/nodes/` Collection-resource of all nodes that belong to the specified organization.
  - [GET] Retrieve all nodes owned by the organization.
  - [POST] Register a new node that is currently unknown to the Managair. This new node will be attributed to the goven organization.
- `/api/v1/organizations/<organization_id>/nodes/timeseries/` Overview of the timeseries reported by the organization's nodes.
  - [GET] Retrieve time range, number of samples, quantities reported for each node. Data is only aggregated for the time slice where the node was owned by the specified organization.
- `/api/v1/organizations/<organization_id>/nodes/fidelity/`
  - [GET] Status list ("fidelity") for all nodes of the organization. The status is updated periodically and indicates if a given node regularly transmits data. In the future, additional information might be added, like battery status or error reports.
- `/api/v1/organizations/<organization_id>/nodes/<node_id>/` Details-resource of the specified node.
  - [GET] Retrieve information about the node. Might include fidelity information.
  - [PUT, PATCH] Update node master data; e.g., node alias or tags (feature request).
  - [DELETE] Remove the node and all samples reported by this node.
- `/api/v1/organizations/<organization_id>/nodes/<node_id>/timeseries/` Detail resource for the time-series reported by the specified node.
  - [GET] Returns the time series for the time period when the node was owned by the specified organization. Supports querying for time slices.
- `/api/v1/organizations/<organization_id>/sites/` Collection-resource of all sites that belong to the organization `organization_id`.
  - [GET] Retrieve the collection.
  - [POST] Create a new site operated by the organization.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/` Details-resource of the specified site.
  - [GET] Rertieve the site resource.
  - [PUT, PATCH] Replace resp. update site master data.
  - [DELETE] Remove the site and all rooms within the site. Does not delete nodes attributed to the site or any of its rooms.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/` Collection-resource of all rooms of a given site.
  - [GET] Retrieve the collection.
  - [POST] Create a new room that is part of the given site.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/<room_id>/` Details-resource of the specifified room.
  - [GET] Retrieve the room resource.
  - [PUT, PATCH] Replace resp. update the room resouce.
  - [DELETE] Remove the room resource. Does not delete nodes attributed to the room.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/<room_id>/timeseries/` A resource for the aggregated time series of the room.
  - [GET] If the room is equipped with several nodes, this aggregation must represent combine the available data meaningfully into a virtual "super-node"; i.e., it should be rather like an average than a sum. If the room is equipped with a single node only, the time series must be exactly equal to this node's time series.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/<room_id>/nodes/` Collection-resource of all node installations in the given room.
  - [GET] Shows current and past installations, as long as the installed sensor is still owned by the given organization.
  - [POST] Associates an already registered node with the room. A node to be associated with a room must not be associated with another room for an overlapping time period.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/<room_id>/nodes/<node_id>/` Details-resource of the specified node.
  - [GET] Redirects to `/api/v1/organizations/<organization_id>/nodes/<node_id>/`.
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