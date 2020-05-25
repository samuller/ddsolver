import os, glob
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

curr_dir = None
curr_img = None
curr_idx = 0


# Create your views here.
def main_page(request):
    global curr_dir, curr_img, curr_idx
    pathname = request.GET.get('pathname', None)

    if pathname is not None:
        if pathname != curr_dir:
            curr_idx = 0
        curr_dir = pathname

    if curr_dir is not None:
        images = glob.glob(curr_dir + '*.gif')
        images = sorted([os.path.basename(img) for img in images])
        curr_img = images[curr_idx]

    context = {curr_dir: curr_dir, curr_img: curr_img}
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

def prev_image(request):
    global curr_idx
    curr_idx = curr_idx - 1
    return HttpResponseRedirect('/')

def next_image(request):
    global curr_idx
    curr_idx = curr_idx + 1
    return HttpResponseRedirect('/')

