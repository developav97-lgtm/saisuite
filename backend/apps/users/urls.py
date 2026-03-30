from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    RefreshView,
    MeView,
    RegisterView,
    UserListCreateView,
    UserDetailView,
    UserMeCompaniesView,
    UserMencionesView,
    SwitchCompanyView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    SoporteTenantsView,
    SoporteSeleccionarTenantView,
    SoporteLiberarTenantView,
    InternalUserListCreateView,
    InternalUserDetailView,
)
from .roles_views import (
    PermissionListView,
    PermissionByModuleView,
    RoleListCreateView,
    RoleDetailView,
)

urlpatterns = [
    path('login/',                     LoginView.as_view(),              name='auth-login'),
    path('logout/',                    LogoutView.as_view(),             name='auth-logout'),
    path('refresh/',                   RefreshView.as_view(),            name='auth-refresh'),
    path('me/',                        MeView.as_view(),                 name='auth-me'),
    path('register/',                  RegisterView.as_view(),           name='auth-register'),
    path('users/',                     UserListCreateView.as_view(),     name='user-list-create'),
    path('users/menciones/',           UserMencionesView.as_view(),      name='user-menciones'),
    path('users/<uuid:pk>/',           UserDetailView.as_view(),         name='user-detail'),
    path('me/companies/',              UserMeCompaniesView.as_view(),    name='user-me-companies'),
    path('switch-company/',            SwitchCompanyView.as_view(),      name='auth-switch-company'),
    path('password-reset/',                     PasswordResetRequestView.as_view(),       name='password-reset-request'),
    path('password-reset/confirm/',             PasswordResetConfirmView.as_view(),       name='password-reset-confirm'),
    path('soporte/tenants/',                    SoporteTenantsView.as_view(),             name='soporte-tenants'),
    path('soporte/seleccionar-tenant/',         SoporteSeleccionarTenantView.as_view(),   name='soporte-seleccionar'),
    path('soporte/liberar-tenant/',             SoporteLiberarTenantView.as_view(),       name='soporte-liberar'),
    path('internal-users/',                     InternalUserListCreateView.as_view(),     name='internal-user-list-create'),
    path('internal-users/<uuid:pk>/',           InternalUserDetailView.as_view(),         name='internal-user-detail'),
    # ── Permisos y Roles granulares ────────────────────────────────────────
    path('permissions/',               PermissionListView.as_view(),     name='permission-list'),
    path('permissions/by-module/',     PermissionByModuleView.as_view(), name='permission-by-module'),
    path('roles/',                     RoleListCreateView.as_view(),     name='role-list-create'),
    path('roles/<int:pk>/',            RoleDetailView.as_view(),         name='role-detail'),
]
