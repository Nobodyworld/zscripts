from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Example
from .forms import ExampleForm

def examples(request):
    examples = Example.objects.all()
    form = ExampleForm()
    return render(request, 'example/examples.html', {'examples': examples, 'form': form})

def add_example(request):
    if request.method == 'POST':
        form = ExampleForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect_url': '/success/'})
        return JsonResponse({'success': False, 'errors': form.errors})
    return render(request, 'example/example_form.html', {'form': form})

def edit_example(request, pk):
    example = get_object_or_404(Example, pk=pk)
    if request.method == 'POST':
        form = ExampleForm(request.POST, instance=example)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect_url': '/examples/'})
        return JsonResponse({'success': False, 'errors': form.errors})
    form = ExampleForm(instance=example)
    return render(request, 'example/example_form.html', {'form': form})

def delete_example(request, pk):
    example = get_object_or_404(Example, pk=pk)
    if request.method == 'POST':
        example.delete()
        return redirect('examples')
    return render(request, 'example/example_confirm_delete.html', {'example': example})
