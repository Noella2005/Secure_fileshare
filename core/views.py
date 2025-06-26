import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse, Http404
from django.core.files.base import ContentFile
from cryptography.fernet import Fernet, InvalidToken
from django.contrib import messages

# Create your views here.
from .forms import UserRegistrationForm, FileUploadForm, FileShareForm
from .models import UploadedFile

# Get the logger
logger = logging.getLogger(__name__)

# Initialize Fernet
fernet = Fernet(settings.FERNET_KEY)

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f"New user registered: {user.username}")
            messages.success(request, f"Welcome {user.username}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard_view(request):
    # Files owned by the user
    owned_files = UploadedFile.objects.filter(owner=request.user).order_by('-uploaded_at')
    
    # Files shared with the user
    shared_files = request.user.shared_files.all().order_by('-uploaded_at')

    upload_form = FileUploadForm()
    share_form = FileShareForm()

    context = {
        'owned_files': owned_files,
        'shared_files': shared_files,
        'upload_form': upload_form,
        'share_form': share_form,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def upload_file_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            # Read file content
            file_content = uploaded_file.read()
            
            # Encrypt file content
            encrypted_content = fernet.encrypt(file_content)
            
            # Create a new file with encrypted content
            encrypted_file = ContentFile(encrypted_content, name=uploaded_file.name)
            
            # Save the file object
            file_instance = UploadedFile(owner=request.user, file=encrypted_file)
            file_instance.save()
            
            logger.info(f"User {request.user.username} uploaded and encrypted file: {uploaded_file.name}")
            messages.success(request, "Your file has been securely uploaded!")
            return redirect('dashboard')
    # This view only handles POST, redirect if accessed via GET
    return redirect('dashboard')

@login_required
def download_file_view(request, file_id):
    file_instance = get_object_or_404(UploadedFile, pk=file_id)

    # Authorization Check: Is the user the owner OR has it been shared with them?
    is_owner = file_instance.owner == request.user
    is_shared_with = request.user in file_instance.shared_with.all()

    if not is_owner and not is_shared_with:
        logger.warning(f"Unauthorized download attempt for file {file_id} by user {request.user.username}")
        raise Http404("You do not have permission to access this file.")

    try:
        # Read the encrypted file content from storage
        encrypted_content = file_instance.file.read()

        # Decrypt the content
        decrypted_content = fernet.decrypt(encrypted_content)

        # Log the successful download
        logger.info(f"User {request.user.username} downloaded file: {file_instance.get_filename()}")

        # Prepare and return the response for download
        response = HttpResponse(decrypted_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_instance.get_filename()}"'
        return response

    except InvalidToken:
        logger.error(f"Failed to decrypt file {file_id}. The encryption key might have changed or the file is corrupt.")
        messages.error(request, "Could not decrypt the file. It may be corrupt or the key is invalid.")
        return redirect('dashboard')
    except Exception as e:
        logger.error(f"An error occurred during file download for file {file_id}: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('dashboard')

@login_required
def share_file_view(request, file_id):
    if request.method == 'POST':
        file_to_share = get_object_or_404(UploadedFile, pk=file_id, owner=request.user)
        form = FileShareForm(request.POST)

        if form.is_valid():
            username_to_share_with = form.cleaned_data['username']
            try:
                user_to_share_with = User.objects.get(username=username_to_share_with)
                
                # Prevent sharing with oneself
                if user_to_share_with == request.user:
                    messages.warning(request, "You cannot share a file with yourself.")
                    return redirect('dashboard')

                file_to_share.shared_with.add(user_to_share_with)
                file_to_share.save()
                
                logger.info(f"User {request.user.username} shared file {file_id} with {username_to_share_with}")
                messages.success(request, f"File shared successfully with {username_to_share_with}.")
            except User.DoesNotExist:
                messages.error(request, "User does not exist.")
        else:
            # Pass form errors to messages framework
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")

    return redirect('dashboard')

@login_required
def delete_file_view(request, file_id):
    # Only the owner can delete a file
    file_to_delete = get_object_or_404(UploadedFile, pk=file_id, owner=request.user)
    
    if request.method == 'POST':
        filename = file_to_delete.get_filename()
        file_to_delete.file.delete() # Deletes the physical file
        file_to_delete.delete()      # Deletes the model instance
        logger.info(f"User {request.user.username} deleted file: {filename}")
        messages.success(request, f"File '{filename}' has been deleted.")

    return redirect('dashboard')