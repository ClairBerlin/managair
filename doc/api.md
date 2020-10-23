# The Managair ReST API

This is a first draft of Managair's API endpoints. It's a design document that describesthe intended API endpoints. It does not describe the API as it is currently implemented.

## API Root and API Structure

Root: `/api/v1/`

Main API branches:

- **User:** Registration, authentication, and user profiles.
- **Inventory:** Resources from the perspective of a specific organization - all their sites, rooms, nodes, etc. Requires login.
- **Data:** Time-series resources for all nodes. Additional aggregation views might be added here in the future. Other endpoints redirect here. Requires login.
- **Public:** Publicly available information on sites and corresponding time series.

All list-resources support paging. HTTP verbs follow the [standardized semantics](https://blog.eq8.eu/article/put-vs-patch.html). See also [here](https://williamdurand.fr/2014/02/14/please-do-not-patch-like-an-idiot/#disqus_thread) and [here](https://stackoverflow.com/questions/28459418/use-of-put-vs-patch-methods-in-rest-api-real-life-scenarios/39338329#39338329)

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

The inventory is organized according to organizations that have one or more rooms with installed sensor nodes. All inventory resources require the user to be logged in.

- `/api/v1/organizations/` List-resource for all organizations.
  - [GET] Users do see only those organizations, including all sub-resources, of which they are a member. If the logged-in user is member of a single organization only, directly redirects to this organization's details.
  - [POST] Register a new organization with the logged-in user as owner.
- `/api/v1/organizations/<organization_id>/` Details-resource of the organization with ID `organization_id`.
  - [GET] Only available if the logged-in user is a member of this organization.
  - [PUT, PATCH] Update organization data.
  - [DELETE] Removes the organization and all assets and data it owns - sites, rooms, nodes, and node time series.
- `/api/v1/organizations/<organization_id>/nodes/` List-resource of all nodes that belong to the specified organization.
  - [GET] Retrieve all nodes owned by the organization.
  - [POST] Register a new node that is currently unknown to the Managair. This new node will be attributed to the goven organization.
- `/api/v1/organizations/<organization_id>/nodes/fidelity`
  - [GET] Status list ("fidelity") for all nodes of the organization. The status is updated automatically and indicates if a given node regularly transmits data. In the future, additional information like battery status and error reports of nodes might be added.
- `/api/v1/organizations/<organization_id>/nodes/timeseries` [GET] List overview of the timeseries reported by the selected nodes; e.g., time range, number of samples, quantities reported.
- `/api/v1/organizations/<organization_id>/nodes/<node_id>/` Details-resource of the specified node.
  - [GET] Retrieve information about the node. Might include fidelity information.
  - [PUT, PATCH] Update node master data; e.g., node alias or tags (feature request).
  - [DELETE] Remove the node and all time series data reported by this node.
- `/api/v1/organizations/<organization_id>/nodes/<node_id>/data/`
  - [GET] List-resource for all data reported and derived from the given node. Redirects to `/api/v1/data/<node_id>/`.
- `/api/v1/organizations/<organization_id>/sites/` List-resource of all sites that belong to the organization `organization_id`.
  - [GET] If the organization has a single site only, redirects to this site's details.
  - [POST] Create a new site operated by the organization.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/` Details-resource of the specified site.
  - [GET] Rertieve the site resource.
  - [PUT, PATCH] Replace resp. update site master data.
  - [DELETE] Remove the site and all rooms within the site. Does not delete nodes attributed to the site or any of its rooms.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/` List-resource of all rooms of a given site.
  - [GET] If a site has a single room only, redirect to the corresponding details view.
  - [POST] Create a new room that is part of the given site. 
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/<room_id>/` Details-resource of the specifified room.
  - [GET] Retrieve the room resource.
  - [PUT, PATCH] Replace resp. update the room resouce.
  - [DELETE] Remove the room resource. Does not delete nodes attributed to the room.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/<room_id>/nodes/` List-resource of all node installations in the given room.
  - [GET] Shows current and past installations, as long as the installed sensor is still owned by the given organization.
  - [POST] Associates an already registered node with the room. A node to be associated with a room must not be associated with another room for an overlapping time period.
- `/api/v1/organizations/<organization_id>/sites/<site_id>/rooms/<room_id>/nodes/<node_id>/` Details-resource of the specified node.
  - [GET] Redirects to `/api/v1/organizations/<organization_id>/nodes/<node_id>/`.
  - [PUT, POST] Replaces resp. updates the association with the room. To end the association with a room, update it with an end date; this preserves the association history.
  - [DELETE] Removes the association with the room. This removes the association history, as if the node was never associated with the room.

## Data

Data is organizaed according to the nodes that reported them. All data resources require the user to be logged in, except for those resources explicitly marked as publicly available. Non-public data resources are available only for nodes that belong to an organization the user is a member of.

- `/api/v1/data/<node_id>/` List-resource that provides an overview of all data resources on the basis of samples reported by the given node. Initially, this is the time series only. When we add additional analyses, they become available here.
  - [GET] Only available if the logged in user is member of the organization that owns the sample,
- `/api/v1/data/<node_id>/timeseries/` Time series resource that including all samples reported by the given node.
  - [GET] Supports querying for time slices and paging.

## Public

Public resources are, well, accessible by the general public without prior login. Public resources are a subset of inventory and data resources listed above, where the resource owner has explicitly marked the resource as publicly available.

## Not-Exposed Resources

We currently do not expose the technical resources for

- Node protocols: Details on capabilities of specific protocols, the reporting format and the quantities that can be reported.
- Node models: Details on specific sensor types, like the manufacturer, the actual senor module used, the quantities measured, etc.

## Versioning