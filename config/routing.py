from django.urls import re_path
from apps.dispatch.consumers import CourierConsumer, OrderTrackingConsumer

websocket_urlpatterns = [
    re_path(r"ws/courier/$", CourierConsumer.as_asgi()),
    re_path(r"ws/orders/(?P<order_id>[0-9a-f-]+)/$", OrderTrackingConsumer.as_asgi()),
]
