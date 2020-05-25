import os
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

curr_dir = None
curr_img = 'p01.gif'


# Create your views here.
def main_page(request, pathname):
    pathname = request.GET.get('pathname', None)

    global curr_dir
    curr_dir = pathname

    context = {curr_dir: pathname}
    return render(request, 'index.html', context)

def main_image(request):
    global curr_dir
    if curr_dir is None or not os.path.exists(curr_dir + curr_img):
        return HttpResponse('')

    import imageio
    im = imageio.imread(curr_dir + curr_img)

    response = HttpResponse(content_type="image/png")
    imageio.imwrite(response, im[:, :], format="png")
    return response

