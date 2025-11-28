import os
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import PROTECT

def user_profile_upload_path(instance, filename):
    base, ext = os.path.splitext(filename)
    nombre_slug = slugify(instance.nombre_completo) or "usuario"
    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    return f"pfp/{nombre_slug}-{timestamp}{ext}"


def product_image_upload_path(instance, filename):
    base, ext = os.path.splitext(filename)
    nombre_slug = slugify(instance.nombre) or "producto"
    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    return f"products/{nombre_slug}-{timestamp}{ext}"

class Usuario(models.Model):
    roles = [
        ('cliente','Cliente'),
        ('vendedor','Vendedor'),
        ('admin','Administrador'),
    ]
    idUsuario = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=100)
    correo = models.EmailField(max_length=100, unique=True)
    contrasena = models.CharField(max_length=50)
    rol = models.CharField(max_length=20, choices=roles)
    fecha_registro = models.DateTimeField(default=timezone.now)
    descripcion = models.TextField(blank=True, null=True)

    foto = models.ImageField(
        upload_to=user_profile_upload_path,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nombre_completo


class Servicio(models.Model):
    idServicio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.IntegerField()
    imagen = models.ImageField(
        upload_to=product_image_upload_path,
        blank=True,
        null=True
    )

    categoria = models.CharField(max_length=50)
    vendedor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="servicios")

    def __str__(self):
        return self.nombre



class Producto(models.Model):
    idProducto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.IntegerField()
    stock = models.IntegerField(default=1)

    imagen = models.ImageField(
        upload_to=product_image_upload_path,
        blank=True,
        null=True
    )

    categoria = models.CharField(max_length=50)
    vendedor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="productos")

    def __str__(self):
        return self.nombre


class ObjetoCarrito(models.Model):
    idObjeto = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    subtotal = models.IntegerField(default=0)

    def calcular_subtotal(self):
        self.subtotal = self.cantidad * self.producto.precio
        self.save()


class Carrito(models.Model):
    idCarrito = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="carritos")
    objetos = models.ManyToManyField(ObjetoCarrito)
    total = models.IntegerField(default=0)

    def calcular_total(self):
        self.total = sum(obj.subtotal for obj in self.objetos.all())
        self.save()


class Direccion(models.Model):
    idDireccion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="direcciones")
    alias = models.CharField(max_length=100, blank=True)  # Ej: "Casa", "Trabajo"
    direccion = models.CharField(max_length=100)          # Texto completo

    def __str__(self):
        # Lo que se mostrará en el admin / templates
        if self.alias:
            return f"{self.alias} - {self.direccion}"
        return self.direccion


class Pedido(models.Model):
    idPedido = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20)
    total = models.IntegerField()
    direccion = models.CharField(max_length=100, blank=True, null=True)
    envio = models.IntegerField(default=0)

    def __str__(self):
        return f"Pedido {self.idPedido}"
    

class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_pedido"
    )
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.IntegerField()
    subtotal = models.IntegerField()

    def __str__(self):
        return f"DetallePedido {self.id} - Pedido {self.pedido_id}"

class Pago(models.Model):
    estados = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    )
    idPago = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    monto = models.IntegerField()
    metodo = models.CharField(max_length=30)
    estado = models.CharField(max_length=20, choices=estados, default='pendiente')
    fecha = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Pago {self.idPago}"


class Mensaje(models.Model):
    idMensaje = models.AutoField(primary_key=True)
    emisor = models.ForeignKey(Usuario, related_name="mensajes_enviados", on_delete=models.CASCADE)
    receptor = models.ForeignKey(Usuario, related_name="mensajes_recibidos", on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Mensaje {self.idMensaje}"


class Notificacion(models.Model):
    idNotificacion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50)
    mensaje = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notificación {self.idNotificacion}"
