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
    SwitchCompanyView,
)

urlpatterns = [
    path('login/',            LoginView.as_view(),           name='auth-login'),
    path('logout/',           LogoutView.as_view(),          name='auth-logout'),
    path('refresh/',          RefreshView.as_view(),         name='auth-refresh'),
    path('me/',               MeView.as_view(),              name='auth-me'),
    path('register/',         RegisterView.as_view(),        name='auth-register'),
    path('users/',            UserListCreateView.as_view(),  name='user-list-create'),
    path('users/<uuid:pk>/',  UserDetailView.as_view(),      name='user-detail'),
    path('me/companies/',     UserMeCompaniesView.as_view(), name='user-me-companies'),
    path('switch-company/',   SwitchCompanyView.as_view(),   name='auth-switch-company'),
]
