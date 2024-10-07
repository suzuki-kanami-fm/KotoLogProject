from django.urls import path
from .views import SignupView, LoginView, LogoutView, UserEditView,UserPageView ,CustomPasswordChangeView, CustomPasswordChangeDoneView

app_name='accounts'
urlpatterns = [
    path('signup/', SignupView.as_view(), name="signup"),
    path('login/', LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user_edit/", UserEditView.as_view(), name="user_edit"),
    path("user_page/", UserPageView.as_view(), name="user_page"),
    path("password_change/", CustomPasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", CustomPasswordChangeDoneView.as_view(), name="password_change_done"),
]