import os, glob
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

import imageio
import numpy as np
from scipy.ndimage import label

curr_dir = None
curr_img = None
curr_idx = 0
curr_xy = None
# Integer scaling only
curr_scale = 4

image_extensions = ['gif', 'jpg', 'png']

# Create your views here.
def main_page(request):
    global curr_dir, curr_img, curr_idx, curr_scale
    pathname = request.GET.get('pathname', None)

    if not is_empty_or_none(pathname):
        if pathname != curr_dir:
            curr_idx = 0
        curr_dir = pathname
        if curr_dir[-1] is not '/':
            curr_dir += '/'

    image_count = 0
    if not is_empty_or_none(curr_dir):
        images = [im for ext in image_extensions for im in glob.glob(curr_dir + '*.' + ext)]
        images = sorted([os.path.basename(img) for img in images])
        image_count = len(images)
        if image_count != 0:
            if curr_idx >= image_count or curr_idx < 0:
                curr_idx = curr_idx % image_count
            curr_img = images[curr_idx]
        else:
            curr_idx = 0
            curr_img = None

    context = {'curr_dir': curr_dir, 'curr_img': curr_img,
               'curr_idx': curr_idx + 1, 'image_count': image_count,
               'curr_scale': curr_scale}
    return render(request, 'index.html', context)


def main_image(request):
    global curr_dir, curr_xy, curr_scale
    if is_empty_or_none(curr_dir) or is_empty_or_none(curr_img) or not os.path.exists(curr_dir + curr_img):
        return HttpResponse('')
    # Load current image
    im = imageio.imread(curr_dir + curr_img)

    im_to_label = im
    # Change zeroes to ones
    im_to_label = np.where(im_to_label == 0, 1, im_to_label)
    # and 255s to zero
    im_to_label = np.where(im_to_label == 255, 0, im_to_label)
    # 4-connectivity structure
    conn = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    # component labelling of each region (separated by zeros)
    labelled, region_count = label(im_to_label, conn)

    # Convert to RGB if grayscale
    if len(im.shape) == 2:
        im = np.stack((im, im, im), axis=-1)
        labelled = np.stack((labelled, labelled, labelled), axis=-1)
    # Color selected area red

    # Color selected area and similar areas
    if curr_xy is not None:
        row, col = curr_xy
        selected_label = labelled[col, row, 0]
        # Color all identical shapes blue
        sel_img = get_label_region(labelled[:, :, 0], selected_label)
        for i in range(region_count):
            lbl_img = get_label_region(labelled[:, :, 0], i)
            if np.array_equal(sel_img > 0, lbl_img > 0):
                im = np.where(labelled == i, [0, 0, 255], im).astype(np.uint8)
        # Color selected area red
        im = np.where(labelled == selected_label, [255, 0, 0], im).astype(np.uint8)

    # Resize image
    im = resize_larger(im, curr_scale)
    response = HttpResponse(content_type="image/png")
    imageio.imwrite(response, im[:, :, :], format="png")
    return response


def prev_image(request):
    global curr_idx, curr_xy
    curr_idx = curr_idx - 1
    curr_xy = None
    return HttpResponseRedirect('/')


def next_image(request):
    global curr_idx, curr_xy
    curr_idx = curr_idx + 1
    curr_xy = None
    return HttpResponseRedirect('/')


def select_xy(request):
    global curr_xy, curr_scale
    if request.method == 'POST':
        x_pos = int(request.POST.get('x'))
        y_pos = int(request.POST.get('y'))
        # Assume integer up-scaling only
        curr_xy = (int(x_pos / curr_scale), int(y_pos / curr_scale))
    return HttpResponseRedirect('/')


def is_empty_or_none(str_value):
    return str_value is None or len(str_value) == 0


def resize_larger(im, scale=2):
    assert scale == int(scale)
    return np.repeat(np.repeat(im, scale, axis=0), scale, axis=1)


def resize_smaller(im, scale=2):
    assert scale == int(scale)
    import skimage.transform
    return skimage.transform.downscale_local_mean(im, (scale, scale))


def get_label_region(label_img, label_value):
    sel_rows, sel_cols = np.nonzero(label_img == label_value)
    return label_img[min(sel_rows):(max(sel_rows) + 1), min(sel_cols):(max(sel_cols) + 1)]
