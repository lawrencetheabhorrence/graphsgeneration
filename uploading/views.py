from django.shortcuts import render, redirect
from .models import Document
from .forms import DocumentForm
from django.conf import settings
from django.core.files import File
from django.http import FileResponse, HttpResponse
import os
import papermill as pm
def notebook_filename(path, suffix, extension):
    filename = os.path.basename(path).split('.')[0].replace(' ', '_') + '_' + suffix + '.' + extension
    return filename

def handlefile(file):
    path = settings.BASE_DIR / f'media/temp/{file.name}'
    with open(path, 'wb+') as f:
        for chunk in file.chunks():
            f.write(chunk)
    with open(path) as f:
        lines = f.readlines()
        cut_until = lines.index('Attendee Details,\n')
        filename = os.path.basename(path).split('.')[0] + '_cleaned.csv'
        with open(settings.BASE_DIR / f'media/documents/{filename}', 'w') as fw:
            fw.write(''.join(lines[cut_until+1:]))

        pm.execute_notebook(str(settings.BASE_DIR / 'uploading/notebooks/attendance.ipynb'),
                   str(settings.BASE_DIR / f'media/temp/{notebook_filename(path, "Attendance", "ipynb")}'),
                   parameters=dict(filepath= str(settings.BASE_DIR / f'media/documents/{filename}')))

        output_filename=str(settings.BASE_DIR / f'media/temp/{notebook_filename(path, "Attendance", "ipynb")}')
        os.system(f'jupyter nbconvert --no-input --to webpdf {output_filename}')

# Create your views here.
def index(request):
    message = 'Upload as many files as you want!'
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            handlefile(request.FILES['docfile'])
            path = settings.BASE_DIR / f'media/temp/{request.FILES["docfile"].name}'
            output_filename=str(settings.BASE_DIR / f'media/temp/{notebook_filename(path, "Attendance", "pdf")}')
            of = open(output_filename, 'rb')
            return FileResponse(of, as_attachment=True, filename='attendance.pdf')
        else:
            message = 'The form is not valid. Fix the following error:'
    else:
        form = DocumentForm()

    documents = Document.objects.all()

    context = {'documents': documents, 'form': form, 'message': message}
    return render(request, 'list.html', context)

