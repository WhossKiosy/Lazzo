from django import forms
from .models import Usuario, Producto, Mensaje
from .widgets import ClearableFileInputES

class RegistroForm(forms.ModelForm):
    contrasena = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ["nombre_completo", "correo", "contrasena", "rol"]


class LoginForm(forms.Form):
    correo = forms.EmailField()
    contrasena = forms.CharField(widget=forms.PasswordInput)


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "descripcion", "precio", "stock", "imagen", "categoria"]


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ["nombre", "descripcion", "precio", "imagen", "categoria"]


class MensajeForm(forms.ModelForm):
    class Meta:
        model = Mensaje
        fields = ["receptor", "contenido"]

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["nombre_completo", "descripcion", "foto"]

        labels = {
            "nombre_completo": "Nombre",
            "descripcion": "Descripción",
            "foto": "Foto de perfil",
        }

        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "foto": forms.FileInput(attrs={
                "accept": "image/*",
            }),
        }
