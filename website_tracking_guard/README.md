# Website Tracking Guard

MVP module for Odoo 17 that disables website visitor tracking by short-circuiting
`website.visitor._get_visitor_from_request()` when a system parameter is enabled.

## System parameter

Key:
website_tracking_guard.disable_tracking

Value:
1

Accepted truthy values:
- 1
- true
- yes
- on

## What this module does

When the parameter is enabled:
- Odoo will return an empty `website.visitor` recordset for frontend requests
- visitor tracking is effectively disabled

## Expected side effects

Features relying on `website.visitor` / `website.track` may stop collecting data.

Examples:
- visitor reporting
- page visit history
- recently viewed logic (if present)

## Rollback

Set:

website_tracking_guard.disable_tracking = 0

or remove the parameter entirely.
``