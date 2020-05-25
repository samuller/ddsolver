from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^image.png$', views.main_image, name='image'),
    url(r'^(?P<pathname>.*)$', views.main_page, name='home')
]
