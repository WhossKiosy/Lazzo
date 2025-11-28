from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout as django_logout
from .models import (
    Usuario, Producto, ObjetoCarrito, Carrito, Pedido, 
    Pago, Mensaje, Notificacion, Direccion, DetallePedido, 
    Servicio, TIPOS_PRODUCTO, CATEGORIAS_PRODUCTO, CATEGORIAS_SERVICIO)
from django.contrib import messages
from django.db.models import Q
import random

from .forms import RegistroForm, LoginForm, ProductoForm, MensajeForm, PerfilForm, ServicioForm

# Create your views here.
 
#------------Usuarios---------------

def home(request):
    productos = Producto.objects.all().order_by('-idProducto')

    categorias_prod_objs = [
        {"tipo": "producto", "slug": value, "label": label}
        for (value, label) in CATEGORIAS_PRODUCTO
    ]
    categorias_serv_objs = [
        {"tipo": "servicio", "slug": value, "label": label}
        for (value, label) in CATEGORIAS_SERVICIO
    ]

    todas_categorias = categorias_prod_objs + categorias_serv_objs
    cantidad = min(4, len(todas_categorias))

    categorias_destacadas = (
        random.sample(todas_categorias, k=cantidad) if cantidad > 0 else []
    )

    return render(
        request,
        "home.html",
        {
            "productos": productos,
            "categorias_destacadas": categorias_destacadas,
        },
    )



def registro(request):
    error_message = None

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            # Pantalla de éxito
            return render(
                request,
                "form_success.html",
                {
                    "title": "Registro",
                    "message": "Tu cuenta ha sido creada correctamente.",
                },
            )
        else:
            error_message = "Hay errores en el formulario. Revisa los campos marcados."
    else:
        form = RegistroForm()

    return render(request, "registro.html", {"form": form, "error_message": error_message})

def login(request):
    error_message = None

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data["correo"]
            contrasena = form.cleaned_data["contrasena"]

            usuario = Usuario.objects.filter(
                correo=correo,
                contrasena=contrasena
            ).first()

            if usuario:
                request.session["usuario_id"] = usuario.idUsuario
                request.session["usuario_nombre"] = usuario.nombre_completo
                request.session["usuario_rol"] = usuario.rol

                return render(
                    request,
                    "form_success.html",
                    {
                        "title": "Inicio de sesión",
                        "message": "Has iniciado sesión correctamente.",
                    },
                )
            else:
                error_message = "Correo o contraseña incorrectos."
        else:
            error_message = "Revisa los campos del formulario."
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form, "error_message": error_message})

def logout(request):
    request.session.flush()
    django_logout(request)
    return redirect("/")

def mi_cuenta(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    usuario = Usuario.objects.get(idUsuario=usuario_id)
    pedidos_recientes = Pedido.objects.filter(usuario=usuario).order_by("-fecha")[:5]

    if request.method == "POST":
        if "eliminar_foto" in request.POST:
            if usuario.foto:
                usuario.foto.delete(save=False)
                usuario.foto = None
                usuario.save()
                messages.success(request, "Tu foto de perfil se eliminó correctamente.")
            else:
                messages.warning(request, "No tienes foto de perfil para eliminar.")
            return redirect("mi_cuenta")

        # Guardar cambios normales
        form = PerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil se ha actualizado con éxito.")
            return redirect("mi_cuenta")
        else:
            messages.error(request, "Hubo un error al actualizar tu perfil. Revisa los campos.")
    else:
        form = PerfilForm(instance=usuario)

    return render(
        request,
        "mi_cuenta.html",
        {
            "usuario": usuario,
            "pedidos_recientes": pedidos_recientes,
            "form": form,
        },
    )

def editar_perfil(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    usuario = Usuario.objects.get(idUsuario=usuario_id)

    if request.method == "POST":
        form = PerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil ha sido actualizado con éxito.")
            return redirect("mi_cuenta")
        else:
            messages.error(request, "Hubo un error al actualizar tu perfil.")
    else:
        form = PerfilForm(instance=usuario)

    return render(request, "editar_perfil.html", {
        "form": form,
        "usuario": usuario
    })

def vendedor_perfil(request, vendedor_id):
    vendedor = Usuario.objects.get(idUsuario=vendedor_id)
    productos = Producto.objects.filter(vendedor=vendedor).order_by('-idProducto')

    return render(request, "vendedor_perfil.html", {
        "vendedor": vendedor,
        "productos": productos,
    })

#-----------CATEGORIAS----------------
def categoria_filtrar(request, categoria):
    productos = Producto.objects.filter(categoria=categoria)

    return render(
        request,
        "categoria_resultados.html",
        {
            "categoria": categoria,
            "productos": productos
        }
    )

def categoria_listado(request, tipo, categoria_slug):
    productos = Producto.objects.filter(tipo=tipo, categoria=categoria_slug)

    # diccionario {value: label} para mostrar nombre bonito
    mapa_categorias = dict(CATEGORIAS_PRODUCTO + CATEGORIAS_SERVICIO)
    categoria_nombre = mapa_categorias.get(categoria_slug, categoria_slug)

    context = {
        "productos": productos,
        "tipo": tipo,
        "categoria_slug": categoria_slug,
        "categoria_nombre": categoria_nombre,
    }
    return render(request, "categoria_listado.html", context)


#-----------SERVICIOS----------------

def servicio_detalle(request, id):
    servicio = Servicio.objects.get(idServicio=id)
    return render(request, "servicio_detalle.html", {"servicio": servicio})

def servicio_crear(request):
    # solo usuarios logueados pueden crear servicios
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    vendedor = Usuario.objects.get(idUsuario=usuario_id)

    if request.method == "POST":
        form = ServicioForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo = form.save(commit=False)
            nuevo.vendedor = vendedor
            nuevo.save()
            return redirect("home")
    else:
        form = ServicioForm()

    return render(request, "servicio_form.html", {"form": form})


#-----------PRODUCTOS----------------

def buscar(request):
    query = request.GET.get("q", "").strip()
    resultados = []

    if query:
        resultados = Producto.objects.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(categoria__icontains=query)
        ).order_by("-idProducto")

    return render(request, "busqueda.html", {
        "query": query,
        "resultados": resultados,
    })

def producto_detalle(request, id):
    producto = Producto.objects.get(idProducto=id)
    return render(request, "producto_detalle.html", {"producto": producto})

def producto_crear(request):
    # solo usuarios logueados pueden crear productos
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    vendedor = Usuario.objects.get(idUsuario=usuario_id)

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo = form.save(commit=False)
            nuevo.vendedor = vendedor
            nuevo.save()
            return redirect("home")
    else:
        form = ProductoForm()

    return render(request, "producto_form.html", {"form": form})

def producto_detalle(request, id):
    producto = Producto.objects.get(idProducto=id)
    return render(request, "producto_detalle.html", {"producto": producto})

def productos_por_categoria(request, tipo, categoria_slug):
    # validar tipo
    if tipo not in ['producto', 'servicio']:
        return redirect('home')

    # mapa slug -> label legible
    categorias_map = dict(CATEGORIAS_PRODUCTO + CATEGORIAS_SERVICIO)
    categoria_nombre = categorias_map.get(categoria_slug, categoria_slug)

    productos = Producto.objects.filter(
        tipo=tipo,
        categoria=categoria_slug
    ).order_by('-idProducto')

    contexto = {
        "tipo": tipo,
        "categoria_slug": categoria_slug,
        "categoria_nombre": categoria_nombre,
        "productos": productos,
    }
    return render(request, "categoria_list.html", contexto)


#-----------CARRITO---------------- 

def carrito_ver(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    usuario = Usuario.objects.get(idUsuario=usuario_id)
    carrito, creado = Carrito.objects.get_or_create(usuario=usuario)

    # subtotales y total actualizado
    for obj in carrito.objetos.all():
        obj.calcular_subtotal()
    carrito.calcular_total()

    objetos = carrito.objetos.select_related("producto")

    # costo de envío
    shipping_cost = 2990 if carrito.total > 0 else 0
    total_con_envio = carrito.total + shipping_cost

    return render(
        request,
        "carrito.html",
        {
            "carrito": carrito,
            "objetos": objetos,
            "shipping_cost": shipping_cost,
            "total_con_envio": total_con_envio,
        },
    )

def carrito_agregar(request, producto_id):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    usuario = Usuario.objects.get(idUsuario=usuario_id)
    carrito, creado = Carrito.objects.get_or_create(usuario=usuario)

    producto = Producto.objects.get(idProducto=producto_id)

    objeto = carrito.objetos.filter(producto=producto).first()

    if objeto:
        objeto.cantidad += 1
        objeto.calcular_subtotal()
    else:
        nuevo = ObjetoCarrito.objects.create(producto=producto, cantidad=1)
        nuevo.calcular_subtotal()
        carrito.objetos.add(nuevo)
    
    carrito.calcular_total()

    return redirect("cart")

def carrito_eliminar(request, objeto_id):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    usuario = Usuario.objects.get(idUsuario=usuario_id)
    carrito = Carrito.objects.filter(usuario=usuario).first()
    if not carrito:
        return redirect("cart")

    objeto = carrito.objetos.get(idObjeto=objeto_id)

    # lo quita del carrito
    carrito.objetos.remove(objeto)  
    # y lo elimina
    objeto.delete()                 
    # actualiza total
    carrito.calcular_total()        

    return redirect("cart")

def carrito_actualizar(request, objeto_id):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    if request.method == "POST":
        cantidad = int(request.POST.get("cantidad", 1))
        if cantidad < 1:
            cantidad = 1

        usuario = Usuario.objects.get(idUsuario=usuario_id)
        carrito = Carrito.objects.get(usuario=usuario)

        objeto = carrito.objetos.get(idObjeto=objeto_id)
        objeto.cantidad = cantidad
        objeto.calcular_subtotal()

        carrito.calcular_total()

    return redirect("cart")


def checkout(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    usuario = Usuario.objects.get(idUsuario=usuario_id)
    carrito, _ = Carrito.objects.get_or_create(usuario=usuario)

    # Carrito vacío → no se puede continuar
    if carrito.total == 0 or carrito.objetos.count() == 0:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

    direcciones = Direccion.objects.filter(usuario=usuario)

    if request.method == "POST":
        direccion_id = request.POST.get("direccion_id", "").strip()
        alias_nueva = request.POST.get("alias_nueva", "").strip()
        direccion_nueva = request.POST.get("direccion_nueva", "").strip()

        direccion_texto = None

        # 1) Si eligió una dirección ya guardada (id numérica)
        if direccion_id and direccion_id not in ("", "nueva"):
            try:
                dir_obj = Direccion.objects.get(
                    idDireccion=direccion_id,
                    usuario=usuario
                )
                direccion_texto = dir_obj.direccion
            except Direccion.DoesNotExist:
                direccion_texto = None

        # 2) Si no hay direcciones o seleccionó explícitamente "nueva"
        if direccion_id == "nueva" or (not direccion_texto and direcciones.count() == 0):
            if not direccion_nueva.strip():
                # Campo de dirección vacío → error y volvemos al template
                messages.error(
                    request,
                    "Debes ingresar una nueva dirección para continuar."
                )
                shipping_cost = 2990 if carrito.total > 0 else 0
                total_con_envio = carrito.total + shipping_cost
                return render(
                    request,
                    "checkout.html",
                    {
                        "carrito": carrito,
                        "objetos": carrito.objetos.select_related("producto"),
                        "shipping_cost": shipping_cost,
                        "total_con_envio": total_con_envio,
                        "direcciones": direcciones,
                    },
                )

            nueva_dir = Direccion.objects.create(
                usuario=usuario,
                alias=alias_nueva if alias_nueva else "",
                direccion=direccion_nueva,
            )
            direccion_texto = nueva_dir.direccion

        # 3) Si aún así no tenemos una dirección válida
        if not direccion_texto:
            messages.error(
                request,
                "Debes seleccionar una dirección guardada o agregar una nueva."
            )
            shipping_cost = 2990 if carrito.total > 0 else 0
            total_con_envio = carrito.total + shipping_cost
            return render(
                request,
                "checkout.html",
                {
                    "carrito": carrito,
                    "objetos": carrito.objetos.select_related("producto"),
                    "shipping_cost": shipping_cost,
                    "total_con_envio": total_con_envio,
                    "direcciones": direcciones,
                },
            )

        # 4) Crear pedido, detalles e inmediato "pago"
        shipping_cost = 2990 if carrito.total > 0 else 0

        pedido = Pedido.objects.create(
            usuario=usuario,
            total=carrito.total + shipping_cost,
            estado="pagado",  # o "pendiente" si luego quieres otro flujo
            direccion=direccion_texto,
            envio=shipping_cost,
        )

        # Detalles del pedido
        for obj in carrito.objetos.select_related("producto"):
            DetallePedido.objects.create(
                pedido=pedido,
                producto=obj.producto,
                cantidad=obj.cantidad,
                precio_unitario=obj.producto.precio,
                subtotal=obj.subtotal,
            )

        # Pago asociado
        Pago.objects.create(
            pedido=pedido,
            monto=pedido.total,
            metodo="Pago en línea",
            estado="pagado",
        )

        # Vaciar carrito
        carrito.objetos.clear()
        carrito.total = 0
        carrito.save()

        messages.success(
            request,
            f"Tu pedido #{pedido.idPedido} se creó y pagó correctamente."
        )
        return redirect("pedidos")

    # GET → mostrar formulario de checkout
    shipping_cost = 2990 if carrito.total > 0 else 0
    total_con_envio = carrito.total + shipping_cost

    return render(
        request,
        "checkout.html",
        {
            "carrito": carrito,
            "objetos": carrito.objetos.select_related("producto"),
            "shipping_cost": shipping_cost,
            "total_con_envio": total_con_envio,
            "direcciones": direcciones,
        },
    )

#-----------PEDIDOS----------------

def crear_pedido(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    usuario = Usuario.objects.get(idUsuario=usuario_id)
    carrito = Carrito.objects.get(usuario=usuario)

    if carrito.total == 0 or carrito.objetos.count() == 0:
        return HttpResponse("Tu carrito está vacío")

    direccion = request.POST.get("direccion", "").strip()
    envio = 2990 if carrito.total > 0 else 0

    pedido = Pedido.objects.create(
        usuario=usuario,
        total=carrito.total + envio,
        estado="pagado",         # o "pendiente" según tu flujo
        # direccion=direccion,
        # envio=envio,
    )

    # Crear líneas de detalle a partir del carrito
    for obj in carrito.objetos.select_related("producto"):
        DetallePedido.objects.create(
            pedido=pedido,
            producto=obj.producto,
            cantidad=obj.cantidad,
            precio_unitario=obj.producto.precio,
            subtotal=obj.subtotal,
        )

        # opcional: actualizar stock
        # obj.producto.stock -= obj.cantidad
        # obj.producto.save()

    # Vaciar carrito
    carrito.objetos.clear()
    carrito.total = 0
    carrito.save()

    messages.success(request, f"Tu pedido #{pedido.idPedido} se ha creado correctamente.")
    return redirect("pedidos")

def pedidos_ver(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    pedidos = Pedido.objects.filter(usuario_id=usuario_id)
    return render(request, "pedidos.html",{"pedidos": pedidos})

def pedido_detalle(request, pedido_id):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    pedido = Pedido.objects.get(idPedido=pedido_id)

    # seguridad: solo el dueño del pedido lo puede ver
    if pedido.usuario.idUsuario != usuario_id:
        return redirect("pedidos")

    items = pedido.detalles.select_related("producto")
    subtotal = sum(item.subtotal for item in items)
    pago = Pago.objects.filter(pedido=pedido).first()

    return render(
        request,
        "pedido_detalle.html",
        {
            "pedido": pedido,
            "items": items,
            "subtotal": subtotal,
            "pago": pago,
        },
    )


#-----------PAGOS----------------

def pagar(request, pedido_id):
    pedido = Pedido.objects.get(idPedido=pedido_id)

    if request.method == "POST":
        metodo = request.POST.get("metodo")

        Pago.objects.create(
            pedido=pedido,
            monto=pedido.total,
            metodo=metodo,
            estado="pagado"
        )

        pedido.estado = "pagado"
        pedido.save()

        return HttpResponse("Pago realizado con éxito.")
    return render(request, "pago.html",{"pedido": pedido})

#-----------MENSAJES----------------

def mensajes_ver(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    usuario = Usuario.objects.get(idUsuario=usuario_id)

    recibidos = usuario.mensajes_recibidos.all()
    enviados = usuario.mensajes_enviados.all()

    return render(request, "mensajes.html", {
        "recibidos": recibidos,
        "enviados": enviados
    })

def mensaje_enviar(request):
    if request.method == "POST":
        usuario_id = request.session.get("usuario_id")
        if not usuario_id:
            return redirect("login")

        form = MensajeForm(request.POST)
        if form.is_valid():
            nuevo = form.save(commit=False)
            nuevo.emisor = Usuario.objects.get(idUsuario=usuario_id)
            nuevo.save()
            return redirect("mensajes")

    return render(request, "mensaje_form.html", {"form": MensajeForm()})

#-----------NOTIFICACIONES----------------

def notificaciones_ver(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    notis = Notificacion.objects.filter(usuario_id=usuario_id)
    return render(request, "notificaciones.html", {"notificaciones": notis})
