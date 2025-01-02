from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import ventas_generales


urlpatterns = [
    path('', views.home, name='home'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('agregar/', views.agregar_producto, name='agregar_producto'),
    path('producto/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('producto/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('punto_de_venta/', views.punto_de_venta, name='punto_de_venta'),
    path('ventas_graficos/', views.ventas_graficos, name='ventas_graficos'),
    path('get_ventas_data/<str:periodo>/', views.get_ventas_por_mes, name='get_ventas_data'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reportes/', views.reportes, name='reportes'),
    path('ventas-generales/', ventas_generales, name='ventas_generales'),
    path('eliminar-venta/<int:venta_id>/', views.eliminar_venta, name='eliminar_venta'),
    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

