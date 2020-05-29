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
    global curr_dir, curr_xy
    if curr_dir is None or not os.path.exists(curr_dir + curr_img):
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
    if curr_xy is not None:
        row, col = curr_xy
        selected_label = labelled[col, row, 0]
        im = np.where(labelled == selected_label, [255, 0, 0], im).astype(np.uint8)

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
    global curr_xy
    if request.method == 'POST':
        x_pos = int(request.POST.get('x'))
        y_pos = int(request.POST.get('y'))
        curr_xy = (x_pos, y_pos)
    return HttpResponseRedirect('/')


def paint_location(nparray, pos_xy, new_value):
    row, col = pos_xy
    img = nparray
    curr_value = np.copy(img[col, row])
    fill_area(img, curr_value, new_value, col, row)


def fill_area(img, area_color, new_color, start_col, start_row):
    """
    Fill area of one color with another color.
    """
    # Follows approach similar to recursion, but with iteration and our own stack
    stack = [(start_col, start_row)]
    while len(stack) != 0:
        col, row = stack.pop()

        max_col, max_row, _ = img.shape
        # Base case: stop at edges of image
        if col < 0 or row < 0 or col >= max_col or row >= max_row:
            continue

        curr_eq = img[col, row] == area_color
        new_eq = img[col, row] == new_color
        # Base case: stop if not the same color, or already the new color
        if not curr_eq.all() or new_eq.all():
            continue

        img[col, row] = new_color
        stack.append((col - 1, row))
        stack.append((col + 1, row))
        stack.append((col, row - 1))
        stack.append((col, row + 1))
