from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout as django_logout
from .models import Usuario, Producto, ObjetoCarrito, Carrito, Pedido, Pago, Mensaje, Notificacion

from .forms import RegistroForm, LoginForm, ProductoForm, MensajeForm

# Create your views here.
 
#------------Usuarios---------------

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

    return render(
        request,
        "mi_cuenta.html",
        {
            "usuario": usuario,
            "pedidos_recientes": pedidos_recientes,
        },
    )


#-----------PRODUCTOS----------------

def home(request):
    productos = Producto.objects.all().order_by('-idProducto')
    return render(request, "home.html", {"productos": productos})

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

#-----------PEDIDOS----------------

def crear_pedido(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    usuario = Usuario.objects.get(idUsuario=usuario_id)
    carrito = Carrito.objects.get(usuario=usuario)

    if carrito.total == 0:
        return HttpResponse("Tu carrito está vacío")
    
    pedido = Pedido.objects.create(
        usuario=usuario,
        total=carrito.total,
        estado = "pendiente"
    )

    #eliminar los productos del carrito

    carrito.objetos.clear()
    carrito.total = 0
    carrito.save()

    return HttpResponse(f"Pedido creado con ID: {pedido.idPedido}")

def pedidos_ver(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    
    pedidos = Pedido.objects.filter(usuario_id=usuario_id)
    return render(request, "pedidos.html",{"pedidos": pedidos})

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