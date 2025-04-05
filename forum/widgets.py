from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe

class IconRadioSelect(forms.RadioSelect):
    # Specify the path to the custom template for rendering a single radio option
    # This path is relative to your Django template directories
    option_template_name = 'widgets/icon_radio_option.html'

    # You could also override the render method if you needed more complex logic
    # for the whole widget, but overriding option_template_name is often sufficient.