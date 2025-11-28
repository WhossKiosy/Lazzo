# main/context_processors.py
from .models import Usuario, Carrito

def carrito_context(request):
    carrito_cantidad = 0
    carrito_items_preview = []
    carrito_total_preview = 0

    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return {
            "carrito_cantidad": carrito_cantidad,
            "carrito_items_preview": carrito_items_preview,
            "carrito_total_preview": carrito_total_preview,
        }

    try:
        usuario = Usuario.objects.get(idUsuario=usuario_id)
    except Usuario.DoesNotExist:
        return {
            "carrito_cantidad": carrito_cantidad,
            "carrito_items_preview": carrito_items_preview,
            "carrito_total_preview": carrito_total_preview,
        }

    carrito = Carrito.objects.filter(usuario=usuario).first()
    if not carrito:
        return {
            "carrito_cantidad": carrito_cantidad,
            "carrito_items_preview": carrito_items_preview,
            "carrito_total_preview": carrito_total_preview,
        }

    objetos = carrito.objetos.select_related("producto")
    carrito_cantidad = sum(obj.cantidad for obj in objetos)
    carrito_total_preview = carrito.total

    # Mostramos máximo 3 ítems en el mini-carrito
    for obj in objetos[:3]:
        producto = obj.producto
        imagen_url = producto.imagen.url if producto.imagen else None
        carrito_items_preview.append({
            "nombre": producto.nombre,
            "cantidad": obj.cantidad,
            "subtotal": obj.subtotal,
            "imagen": imagen_url,
        })

    return {
        "carrito_cantidad": carrito_cantidad,
        "carrito_items_preview": carrito_items_preview,
        "carrito_total_preview": carrito_total_preview,
    }
