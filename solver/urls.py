from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.main_page, name='home'),
    url(r'^image.png$', views.main_image, name='image'),
    url(r'^next_img$', views.next_image, name='next'),
    url(r'^prev_img$', views.prev_image, name='prev'),
    url(r'^select_xy', views.select_xy, name='select_xy'),
]
