from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FarmViewSet, ScenarioViewSet, RunViewSet, health
from .solar_views import SolarRunViewSet
router = DefaultRouter()
router.register("farms", FarmViewSet)
router.register("scenarios", ScenarioViewSet)
router.register("scenario-runs", RunViewSet)
router.register("solar-runs", SolarRunViewSet)
urlpatterns = [path("health/", health), path("", include(router.urls))]
