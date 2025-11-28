from django.forms.widgets import ClearableFileInput

class ClearableFileInputES(ClearableFileInput):
    initial_text = "Foto actual"
    input_text = "Subir nueva foto"
    clear_checkbox_label = "Eliminar foto"