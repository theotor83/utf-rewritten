from .models import *

# Context provider functions
# Naming convention: <theme_name>__<template>__processor
def modern__index__processor(request, base_context):
    """Testing hello world context processor for the modern theme."""
    
    return {
        'hello_world': 'Hello World, modern',
    }

def test__index__processor(request, base_context):
    """Testing hello world context processor for the test theme."""
    
    return {
        'hello_world': 'Hello World, test',
    }





# Registry structure: theme: {template_filename: context_provider_function}
THEME_CONTEXT_REGISTRY = {
    'modern': {
        'index.html': modern__index__processor,
        # ... more views as needed
    },
    'test': {
        'index.html': test__index__processor,
        # ... more views as needed
    }
}





# Main function to get additional context
def get_theme_context(request, theme_name, base_context, template_name):
    """Use template name to identify which context provider to use"""
    theme_providers = THEME_CONTEXT_REGISTRY.get(theme_name, {})
    context_provider = theme_providers.get(template_name)
    
    if context_provider:
        try:
            return context_provider(request, base_context)
        except Exception as e:
            print(f"Error getting theme context: {e}")
            return {}
    else:
        return {}