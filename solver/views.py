import os, glob
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

import numpy as np

curr_dir = None
curr_img = None
curr_idx = 0
curr_xy = None


# Create your views here.
def main_page(request):
    global curr_dir, curr_img, curr_idx
    pathname = request.GET.get('pathname', None)

    if pathname is not None:
        if pathname != curr_dir:
            curr_idx = 0
        curr_dir = pathname

    image_count = 0
    if curr_dir is not None:
        images = glob.glob(curr_dir + '*.gif')
        images.extend(glob.glob(curr_dir + '*.jpg'))
        images = sorted([os.path.basename(img) for img in images])
        image_count = len(images)
        if curr_idx >= image_count or curr_idx < 0:
            curr_idx = curr_idx % image_count
        curr_img = images[curr_idx]

    context = {'curr_dir': curr_dir, 'curr_img': curr_img,
               'curr_idx': curr_idx + 1, 'image_count': image_count}
    return render(request, 'index.html', context)

def main_image(request):
    global curr_dir
    if curr_dir is None or not os.path.exists(curr_dir + curr_img):
        return HttpResponse('')

    import imageio
    im = imageio.imread(curr_dir + curr_img)
    # Convert to RGB if grayscale
    if len(im.shape) == 2:
        im = np.stack((im, im, im), axis=-1)

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

def select_xy(request):
    global curr_xy
    if request.method == 'POST':
        x_pos = int(request.POST.get('x'))
        y_pos = int(request.POST.get('y'))
        curr_xy = (x_pos, y_pos)
    print(curr_xy)
    return HttpResponseRedirect('/')
