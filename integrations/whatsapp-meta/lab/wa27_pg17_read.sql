-- WA27 synthetic role only; variable wa27_role is a CI-owned literal.
\set ON_ERROR_STOP on
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL ROLE :wa27_role;
SELECT jsonb_build_object(
 'stage', :'wa27_stage',
 'observed_role',current_user::text,
 'scope',(SELECT payload FROM wa27_lab.scopes WHERE selection_ref='fixture_selection_100'),
 'policy',(SELECT payload FROM wa27_lab.policies WHERE selection_ref='fixture_selection_100'),
 'catalog',(SELECT payload FROM wa27_lab.catalogs WHERE selection_ref='fixture_selection_100'),
 'visible_scopes',(SELECT COUNT(*) FROM wa27_lab.scopes),
 'cross_tenant_scopes',(SELECT COUNT(*) FROM wa27_lab.scopes WHERE reader_role <> current_user::name),
 'can_write',has_table_privilege(current_user,'wa27_lab.scopes','UPDATE')
)::text;
COMMIT;
