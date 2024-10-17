from django.urls import path
from .views import (SignupView, LoginView, LogoutView, UserEditView,UserPageView ,
    CustomPasswordChangeView, CustomPasswordChangeDoneView,
    InvitationUrlView,FamilyDeleteView,ChildDeleteView)

app_name='accounts'
urlpatterns = [
    path('signup/', SignupView.as_view(), name="signup"),
    path('signup/<uuid:uuid>/', SignupView.as_view(), name='signup_with_invite'),
    path('login/', LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user_edit/", UserEditView.as_view(), name="user_edit"),
    path("user_page/", UserPageView.as_view(), name="user_page"),
    path("password_change/", CustomPasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", CustomPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("invitation_url/", InvitationUrlView.as_view(), name="invitation_url"),
    path('family/delete/', FamilyDeleteView.as_view(), name='family_delete'),
    path('child/delete/<int:child_id>/', ChildDeleteView.as_view(), name='child_delete'),
]