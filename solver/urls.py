from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.main_page, name='home'),
    url(r'^image.png$', views.main_image, name='image')
]
