from django.shortcuts import render
from django.http import HttpResponse

curr_dir = ''
curr_img = ''

# Create your views here.
def main_page(request):
    context = {}
    return render(request, 'index.html', context)

def main_image(request):
    import imageio
    im = imageio.imread(curr_dir + curr_img)

    response = HttpResponse(content_type="image/png")
    imageio.imwrite(response, im[:, :], format="png")
    return response

