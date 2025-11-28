from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth import logout as django_logout
from .models import (
    Usuario, Producto, ObjetoCarrito, Carrito, Pedido, 
    Pago, Mensaje, Notificacion, Direccion, DetallePedido, 
    Servicio, Favorito, TIPOS_PRODUCTO, CATEGORIAS_PRODUCTO, CATEGORIAS_SERVICIO)
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


def acerca(request):
    return render(request, 'acerca.html')


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

def mi_perfil(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    usuario = get_object_or_404(Usuario, idUsuario=usuario_id)

    if usuario.rol == "vendedor":
        productos = Producto.objects.filter(vendedor=usuario).order_by("-idProducto")
        return render(request, "vendedor_perfil.html", {
            "vendedor": usuario,
            "productos": productos,
        })

    return render(request, "cliente_perfil.html", {
        "usuario": usuario,
    })
    
def vendedor_perfil(request, vendedor_id):
    vendedor = get_object_or_404(Usuario, idUsuario=vendedor_id)
    productos = Producto.objects.filter(vendedor=vendedor).order_by("-idProducto")

    es_propietario = request.session.get("usuario_id") == vendedor_id

    return render(
        request,
        "vendedor_perfil.html",
        {
            "vendedor": vendedor,
            "productos": productos,
            "es_propietario": es_propietario,
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


def favorito_toggle(request, producto_id):
    """
    Añade o quita un producto de los favoritos del usuario logueado.
    """
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        messages.error(request, "Debes iniciar sesión para usar favoritos.")
        return redirect("login")

    usuario = Usuario.objects.get(idUsuario=usuario_id)
    producto = get_object_or_404(Producto, idProducto=producto_id)

    favorito, creado = Favorito.objects.get_or_create(
        usuario=usuario,
        producto=producto
    )

    if creado:
        messages.success(request, "Producto añadido a tus favoritos.")
    else:
        favorito.delete()
        messages.info(request, "Producto eliminado de tus favoritos.")

    return redirect("producto_detalle", id=producto.idProducto)


def favoritos(request):
    """
    Lista de productos favoritos del usuario logueado.
    """
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    usuario = Usuario.objects.get(idUsuario=usuario_id)
    favoritos_qs = Favorito.objects.filter(usuario=usuario).select_related("producto")

    productos = [f.producto for f in favoritos_qs]

    return render(request, "favoritos.html", {"productos": productos})


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


def catalogo(request):
    # --- Filtros desde la URL (GET) ---
    min_precio = request.GET.get("min_precio", "").strip()
    max_precio = request.GET.get("max_precio", "").strip()
    orden = request.GET.get("orden", "relevancia")  # relevancia / precio_asc / precio_desc / recientes

    # Base: todos los productos
    productos = Producto.objects.all()

    # Filtro por rango de precios
    if min_precio.isdigit():
        productos = productos.filter(precio__gte=int(min_precio))
    if max_precio.isdigit():
        productos = productos.filter(precio__lte=int(max_precio))

    # Ordenamiento
    if orden == "precio_asc":
        productos = productos.order_by("precio")
    elif orden == "precio_desc":
        productos = productos.order_by("-precio")
    elif orden == "recientes":
        productos = productos.order_by("-idProducto")
    else:
        # "relevancia": por ahora usamos también más recientes
        productos = productos.order_by("-idProducto")

    # ---------- PAGINACIÓN ----------
    paginator = Paginator(productos, 12)  # 12 productos por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ---------- AGRUPAR POR CATEGORÍA (solo los de la página actual) ----------
    mapa_categorias = dict(CATEGORIAS_PRODUCTO + CATEGORIAS_SERVICIO)

    productos_por_categoria = {}
    for p in page_obj.object_list:
        categoria_slug = p.categoria
        tipo = p.tipo  # "producto" o "servicio"

        if categoria_slug not in productos_por_categoria:
            productos_por_categoria[categoria_slug] = {
                "nombre": mapa_categorias.get(categoria_slug, categoria_slug),
                "tipo": tipo,
                "productos": []
            }

        productos_por_categoria[categoria_slug]["productos"].append(p)

    context = {
        "page_obj": page_obj,
        "productos_por_categoria": productos_por_categoria,
        "min_precio": min_precio,
        "max_precio": max_precio,
        "orden": orden,
    }
    return render(request, "catalogo.html", context)


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
    producto = get_object_or_404(Producto, idProducto=id)

    es_favorito = False
    usuario_id = request.session.get("usuario_id")
    if usuario_id:
        es_favorito = Favorito.objects.filter(
            usuario_id=usuario_id,
            producto=producto
        ).exists()

    return render(
        request,
        "producto_detalle.html",
        {
            "producto": producto,
            "es_favorito": es_favorito,
        },
    )

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


def producto_editar(request, producto_id):
    """
    Solo el vendedor dueño del producto puede editarlo.
    """
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    producto = get_object_or_404(Producto, idProducto=producto_id)

    # Verificamos que el producto pertenezca al usuario logueado
    if producto.vendedor_id != usuario_id:
        return HttpResponse("No tienes permiso para editar este producto.", status=403)

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("vendedor_perfil", vendedor_id=usuario_id)
    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        "producto_edit_form.html",
        {
            "form": form,
            "producto": producto,
        },
    )

def producto_eliminar(request, producto_id):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    producto = get_object_or_404(Producto, idProducto=producto_id)

    if producto.vendedor_id != usuario_id:
        return HttpResponse("No tienes permiso para eliminar este producto.", status=403)

    if request.method == "POST":
        producto.delete()
        messages.success(request, "Producto eliminado correctamente.")
        return redirect("mi_perfil")
    
    return redirect("producto_editar", producto_id=producto.idProducto)

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
