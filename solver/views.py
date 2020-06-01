import os, glob
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

import imageio
import numpy as np
from scipy.ndimage import label
import bitarray, bitarray.util

# Constants
image_extensions = ['gif', 'jpg', 'png']
# Globals
curr_dir = None
curr_img = None
curr_idx = 0
curr_xy = None
# Integer scaling only
curr_scale = 4


shape_transforms = [
    # rows, cols, before, after
    (7, 5, '1c9f27c9c', '000e03800'),
    (7, 5, '109f8fc84', '394a5294e'),
    (7, 5, '7e1084210', '119c2109f'),
    (7, 5, '709485e1c', '30422210e'),
    (7, 5, '7e1f85e10', '30426084c'),
    (7, 5, '5e1c8721c', '08ca53c42'),
    (7, 5, '77b58709f', '39086084c'),
    # (7, 5, '057d2729c', '21087294e'),
    (7, 5, '74e544210', '3c2111084'),
    (7, 5, '5f1ca7e9f', '394a7294e'),
    (7, 5, '0535afc9c', '394a70842'),
    # + - * / . ... _
    (7, 5, '5e14f5217', '0084f9080'),
    (7, 5, '7d5087e10', '0000f8000'),
    (7, 5, '7c35ed61f', '022a22a20'),
    # (7, 5, '1c958d49c', '0080f8080'),
    # (7, 5, '1c214421c', '0000011c4'),
    (7, 5, '5e1727210', '000000015'),
    (7, 5, '109f85e17', '07b2aa6f0'),
]


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

    # Randomly color each region
    # import random
    # for i in range(region_count):
    #     color = [int(random.random() * 255), int(random.random() * 255), int(random.random() * 255)]
    #     im = np.where(labelled == i, color, im).astype(np.uint8)

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

    for transform in shape_transforms:
        tr_rows, tr_cols, tr_before, tr_after = transform
        before_arr = hex_str_to_nparr(tr_before, (tr_rows, tr_cols))
        after_arr = hex_str_to_nparr(tr_after, (tr_rows, tr_cols))
        update_matching_shapes(im, labelled, before_arr, after_arr)

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


def update_matching_shapes(col_img, lbl_img, before_shape, after_shape):
    """
    Update color image to replace shapes by matching them in the label image.
    """
    assert len(col_img.shape) == 3
    assert col_img.shape == lbl_img.shape
    assert before_shape.shape == after_shape.shape
    assert before_shape.dtype == np.bool_
    assert before_shape.dtype == after_shape.dtype

    labels = np.unique(lbl_img)

    after_col_img = np.stack((after_shape, after_shape, after_shape), axis=-1)
    after_col_img = 255 * np.invert(after_col_img).astype(np.uint8)
    for idx in labels:
        lbl_shape = get_label_region(lbl_img[:, :, 0], idx, dim=before_shape.shape)
        if np.array_equal(lbl_shape > 0, before_shape):
            sub_img = get_subregion_matching_label_region(col_img, lbl_img[:, :, 0], idx, dim=before_shape.shape)
            sub_img[:] = after_col_img
            # im[np.nonzero(labelled == idx)] = lbl_img.astype(np.uint8).flatten()
            # im = np.where(labelled == i, [128, 0, 128], im).astype(np.uint8)


def get_label_region(label_img, label_value, dim=None):
    """
    Get smallest rectangular region including all labels of the given value in the given label image.

    Optional dimensions can be provided, in which case the rectangle will be enlarged (or shrunk)
    to match those dimensions by keeping the initial rectangle in the top-left corner.
    """
    assert len(label_img.shape) == 2
    sel_rows, sel_cols = np.nonzero(label_img == label_value)
    min_row = min(sel_rows)
    max_row = max(sel_rows) + 1
    min_col = min(sel_cols)
    max_col = max(sel_cols) + 1
    if dim is not None:
        assert len(dim) == 2
        max_row = min_row + dim[0]
        max_col = min_col + dim[1]
    return label_img[min_row:max_row, min_col:max_col]


def get_subregion_matching_label_region(col_img, label_img, label_value, dim=None):
    """
    Get the subregion in the color image that corresponds with the smallest rectangle in the label image
    that contains all instances of the label values.
    """
    assert len(col_img.shape) == 3
    assert len(label_img.shape) == 2
    assert col_img.shape[0] == label_img.shape[0]
    assert col_img.shape[1] == label_img.shape[1]
    lbl_rows, lbl_cols = np.nonzero(label_img == label_value)
    min_row = min(lbl_rows)
    max_row = max(lbl_rows) + 1
    min_col = min(lbl_cols)
    max_col = max(lbl_cols) + 1
    if dim is not None:
        assert len(dim) == 2
        max_row = min_row + dim[0]
        max_col = min_col + dim[1]
    return col_img[min_row:max_row, min_col:max_col, :]


def get_label_region_min_max(label_img, label_value):
    assert len(label_img.shape) == 2
    lbl_rows, lbl_cols = np.nonzero(label_img == label_value)
    return ((min(lbl_rows), max(lbl_rows) + 1), (min(lbl_cols), max(lbl_cols) + 1))


def hex_str_to_nparr(hex_str, arr_shape):
    np_arr = np.array(bitarray.util.hex2ba(hex_str).tolist())
    np_arr = np_arr[-(arr_shape[0]*arr_shape[1]):]
    np_arr = np_arr.reshape(arr_shape)
    return np_arr
