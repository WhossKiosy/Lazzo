from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.contrib.auth import logout as django_logout

from .forms import RegistroForm, LoginForm, ProductoForm, MensajeForm

# Create your views here.
def home(request):
    productos = Producto.objects.all()
    return render(request, "home.html", {"productos": productos})


def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("Registro completado con éxito")
    else:
        form = RegistroForm()

    return render(request, "registro.html", {"form": form})


def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data["correo"]
            contrasena = form.cleaned_data["contrasena"]

            usuario = Usuario.objects.filter(correo=correo, contrasena=contrasena).first()

            if usuario:
                request.session["usuario_id"] = usuario.idUsuario
                return HttpResponse("Inicio de sesión correcto")
            else:
                return HttpResponse("Credenciales inválidas")

    return render(request, "login.html", {"form": LoginForm()})

def logout(request):
    if "usuario_id" in request.session:
        del request.session["usuario_id"]
    django_logout(request)
    return HttpResponse("Sesión cerrada correctamente")
