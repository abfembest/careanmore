"""Permission matrix for the dashboard.

Rows are areas, columns are actions. A Role stores {area: [actions]}.
Superusers always have every permission.
"""
ACTIONS = [('view', 'View'), ('add', 'Add'), ('change', 'Edit'), ('delete', 'Delete')]

# area key -> (label, actions that make sense for it)
AREAS = {
    'dashboard': ('Dashboard overview', ['view']),
    'service_users': ('Service users', ['view', 'add', 'change', 'delete']),
    'staff': ('Staff', ['view', 'add', 'change', 'delete']),
    'shifts': ('Shifts', ['view', 'add', 'change', 'delete']),
    'onboarding': ('Onboarding checklists', ['view', 'change']),
    'enquiries': ('Website enquiries', ['view', 'change', 'delete']),
    'site': ('Website content & settings', ['view', 'add', 'change', 'delete']),
    'users': ('Users & roles', ['view', 'add', 'change', 'delete']),
}
AREA_ACTIONS = {k: v[1] for k, v in AREAS.items()}

ALL = {k: list(v) for k, v in AREA_ACTIONS.items()}
DEFAULT_ROLES = [
    ('Administrator', 'Full access to everything, including users and roles.', ALL, True),
    ('Registered manager', 'Runs care operations and the website. Can view users.', {
        **{k: v for k, v in ALL.items() if k != 'users'}, 'users': ['view']}, False),
    ('Care coordinator', 'Plans care: service users, shifts and onboarding.', {
        'dashboard': ['view'], 'service_users': ['view', 'add', 'change'], 'staff': ['view'],
        'shifts': ['view', 'add', 'change', 'delete'], 'onboarding': ['view', 'change'],
        'enquiries': ['view', 'change']}, False),
    ('Office administrator', 'Handles enquiries and keeps the website up to date.', {
        'dashboard': ['view'], 'enquiries': ['view', 'change', 'delete'],
        'site': ['view', 'add', 'change', 'delete']}, False),
    ('Care worker', 'Read-only access to shifts and the people they support.', {
        'service_users': ['view'], 'shifts': ['view']}, False),
]


def get_role(user):
    """The user's role, cached on the user object for the request."""
    if not hasattr(user, '_careapp_role'):
        assignment = getattr(user, 'dashboard_role', None) if user.is_authenticated else None
        user._careapp_role = assignment.role if assignment else None
    return user._careapp_role


def can(user, area, action='view'):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return action in AREA_ACTIONS.get(area, ())
    role = get_role(user)
    return bool(role and role.allows(area, action))


def allowed(user):
    """{area: set(actions)} for templates, e.g. {% if 'add' in perms_for.shifts %}."""
    return {area: {a for a in actions if can(user, area, a)} for area, actions in AREA_ACTIONS.items()}


def has_any_access(user):
    return any(allowed(user).values())
