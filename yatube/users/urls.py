from django.urls import path

from . import views

urlpatterns = [
    # path('signup/', views.SignUp.as_view(), name='signup'),
    path('', views.dashboard, name='dashboard'),
    # #path('passowrd-change/', 'django.contrib.auth.views.password_change',
    #      name='password_change'),
    # path('passowrd-change/done/',
    #      'django.contrib.auth.views.password_change_done',
    #      name='password_change_done'),
    path('signup/', views.signup, name='signup')
    # path('login/', views.user_login, name='login')

]
