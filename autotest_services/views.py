from django.shortcuts import render


def ows_post_test(request):
    return render(request, "autotest_services/ows_post_test.html")
