from django.shortcuts import render
from django.conf import settings

def home_view(request):
    return render(request, 'index.html', {
        # Pass the GROQ API key to the template for frontend use
        'groq_api_key': settings.GROQ_API_KEY
    })