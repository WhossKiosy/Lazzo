from django.db import models
from django.utils import timezone


class Usuario(models.Model):
    roles = [
        ('cliente','Cliente')
        ('vendedor','Vendedor')
        ('admin','Administrador')
    ]
    idUsuario = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=50)
    rol = models.CharField(max_length=20, choices=roles)
    fecha_registro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nombre_completo



class Producto(models.Model):
    idProducto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.IntegerField()
    stock = models.IntegerField(default=1)
    imagen = models.CharField(max_length=100)
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

class Pedido(models.Model):
    idPedido = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20)
    total = models.IntegerField()

    def __str__(self):
        return f"Pedido {self.idPedido}"


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
