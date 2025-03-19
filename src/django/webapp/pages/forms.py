from django import forms

class ImageUploadForm(forms.Form):
    image = forms.ImageField(required=True)
    username = forms.CharField(max_length=255)
    car_name = forms.CharField(max_length=255)
