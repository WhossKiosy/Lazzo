from django import forms
from .models import Usuario, Producto, Mensaje


class RegistroForm(forms.ModelForm):
    contrasena = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ["nombre", "correo", "contrasena", "rol"]


class LoginForm(forms.Form):
    correo = forms.EmailField()
    contrasena = forms.CharField(widget=forms.PasswordInput)


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "descripcion", "precio", "stock", "imagen", "categoria"]


class MensajeForm(forms.ModelForm):
    class Meta:
        model = Mensaje
        fields = ["receptor", "contenido"]
