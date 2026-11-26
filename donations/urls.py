
from django.urls import path

from . import views


app_name = "donations"

urlpatterns = [
    path(
        "",
        views.donation_page,
        name="page"
    ),
    path(
        "payment/",
        views.donation_payment,
        name="payment"
    ),
]
