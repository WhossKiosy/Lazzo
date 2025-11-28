from django.contrib import admin
from django.urls import path
from main import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    # Home
    path('', views.home, name="home"),
    path("buscar/", views.buscar, name="buscar"),
    path("categoria/<str:tipo>/<str:categoria_slug>/", views.productos_por_categoria, name="categoria_list"),
    path(
            "categoria/<str:tipo>/<str:categoria_slug>/",
            views.categoria_listado,
            name="categoria_listado",
        ),
    path('acerca/', views.acerca, name='acerca'),
    path('catalogo/', views.catalogo, name='catalogo'),

    # Autenticación
    path('login/', views.login, name="login"),
    path('signup/', views.registro, name="registro"),
    path('registro/', views.registro, name="signup"),
    path('logout/', views.logout, name="logout"),

    # Carrito
    path("cart/", views.carrito_ver, name="cart"),
    path("cart/add/<int:producto_id>/", views.carrito_agregar, name="cart_add"),
    path("cart/update/<int:objeto_id>/", views.carrito_actualizar, name="cart_update"),
    path("cart/delete/<int:objeto_id>/", views.carrito_eliminar, name="cart_delete"),

    # Cuenta del usuario
    path("account/", views.mi_cuenta, name="mi_cuenta"),
    path("mi-perfil/", views.mi_perfil, name="mi_perfil"),

    # Pedidos
    path("pedidos/", views.pedidos_ver, name="pedidos"),
    path("pedido/crear/", views.crear_pedido, name="crear_pedido"),
    path("checkout/", views.checkout, name="checkout"),
    path("pedido/<int:pedido_id>/", views.pedido_detalle, name="pedido_detalle"),

    # Mensajes
    path("mensajes/", views.mensajes_ver, name="mensajes"),
    path("mensajes/enviar/", views.mensaje_enviar, name="mensaje_enviar"),

    # Notificaciones
    path("notificaciones/", views.notificaciones_ver, name="notificaciones"),

    # Productos (solo vendedor)
    path("producto/nuevo/", views.producto_crear, name="producto_crear"),
    path("producto/<int:id>/", views.producto_detalle, name="producto_detalle"),
    path("producto/<int:producto_id>/editar/", views.producto_editar, name="producto_editar"),
    path("producto/<int:producto_id>/eliminar/", views.producto_eliminar, name="producto_eliminar"),

    # Favoritos
    path("favoritos/", views.favoritos, name="favoritos"),
    path("favoritos/toggle/<int:producto_id>/", views.favorito_toggle, name="favorito_toggle"),

    # Perfil tienda/vendedor
    path("vendedor/<int:vendedor_id>/", views.vendedor_perfil, name="vendedor_perfil"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
