from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.main_page, name='home'),
    url(r'^image.png$', views.main_image, name='image'),
    url(r'^pattern(?P<idx>[0-9]+).png$', views.pattern_img, name='pattern'),
    url(r'^next_img$', views.next_image, name='next'),
    url(r'^prev_img$', views.prev_image, name='prev'),
    url(r'^select_xy', views.select_xy, name='select_xy'),
    url(r'^set_mode', views.set_mode, name='set_mode'),
]
