from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now, localtime
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.utils.timezone import now, localtime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import fitz
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from .models import CreditRequest
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .forms import RegisterForm
from .models import Profile, DocumentScan, ScanRequest
from django.contrib.auth import get_user_model
from sentence_transformers import SentenceTransformer, util
import torch
from django.db.models import Count, Sum
from collections import Counter
import re

# Load the Sentence Transformer model (BERT-based)
model = SentenceTransformer("all-MiniLM-L6-v2")

User = get_user_model()


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, credits=20)  # Default 20 credits
            login(request, user)
            return redirect("profile")
        else:
            messages.error(request, "Registration failed. Please check your details.")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        username_or_email = request.POST["username"]
        password = request.POST["password"]

        # Support email or username login
        user = User.objects.filter(email=username_or_email).first() or User.objects.filter(
            username=username_or_email).first()
        if user:
            user = authenticate(request, username=user.username, password=password)
            if user:
                login(request, user)
                return redirect("profile")

        messages.error(request, "Invalid username/email or password.")

    return render(request, "login.html")

@login_required
def profile(request):
    user = request.user

    if user.is_superuser:  # Check if user is an admin
        credit_requests = CreditRequest.objects.filter(status="pending").order_by("-created_at")
        return render(request, "admin_profile.html", {"credit_requests": credit_requests})

    else:
        profile = user.profile
        last_scan = DocumentScan.objects.filter(user=user).order_by("-scanned_at").first()
        if not last_scan or localtime(last_scan.scanned_at).date() < now().date():
            profile.credits = 20  # Reset to 20 daily scans
            profile.save()

        past_scans = DocumentScan.objects.filter(user=user).order_by("-scanned_at")[:10]  # Last 10 scans
        requests = CreditRequest.objects.filter(user=user).order_by("-created_at")[:5]  # Last 5 requests

        return render(
            request,
            "profile.html",
            {"profile": profile, "past_scans": past_scans, "requests": requests},
        )


@login_required
def request_credits(request):
    if request.method == "POST":
        if request.user.profile.credits > 0:
            messages.warning(request, "You can only request credits when your current credits are exhausted.")
        else:
            existing_request = CreditRequest.objects.filter(user=request.user, status="Pending").exists()
            if existing_request:
                messages.warning(request, "You already have a pending request.")
            else:
                CreditRequest.objects.create(user=request.user, requested_credits=20, status="pending")
                messages.success(request, "Your request has been submitted.")
        return redirect("profile")


@login_required
def manage_credit_requests(request, request_id, action):
    if not request.user.is_superuser:
        return redirect("profile")  # Only admins can manage requests

    try:
        scan_request = CreditRequest.objects.get(id=request_id, status="pending", approved=False, denied=False)
    except CreditRequest.DoesNotExist:
        messages.error(request, "Credit request not found or already processed.")
        return redirect("profile")

    user_profile = getattr(scan_request.user, 'profile', None)
    if user_profile is None:
        # Create a profile if it does not exist
        user_profile = Profile.objects.create(user=scan_request.user, credits=0)

    if action == "approve":
        user_profile.credits += 20  # Grant 20 extra credits
        user_profile.save()
        scan_request.status = "approved"
        scan_request.approved = True
        messages.success(request, f"Approved 20 credits for {scan_request.user.username}")
    elif action == "deny":
        scan_request.status = "denied"
        scan_request.denied = True
        messages.warning(request, f"Denied request from {scan_request.user.username}")

    scan_request.save()

    pending_requests = CreditRequest.objects.filter(status="pending", approved=False, denied=False)
    return render(request, "admin_profile.html", {"credit_requests": pending_requests})

def user_logout(request):
    logout(request)
    return redirect("login")



@login_required
@csrf_exempt
def scan_document(request):
    if request.method == "POST":
        if request.user.profile.credits <= 0:
            return JsonResponse({"error": "Insufficient credits"}, status=400)

        uploaded_file = request.FILES["document"]
        file_path = default_storage.save(f"documents/{uploaded_file.name}", ContentFile(uploaded_file.read()))

        request.user.profile.credits -= 1
        request.user.profile.save()

        document_text = ""
        with fitz.open(default_storage.path(file_path)) as pdf_document:
            for page in pdf_document:
                document_text += page.get_text()

        DocumentScan.objects.create(user=request.user, document_name=uploaded_file.name, content=document_text)
        matching_docs = get_matching_documents(document_text)

        return render(request, "scan_result_popup.html", {
            "message": "Document scanned successfully",
            "file_path": file_path,
            "matches": matching_docs
        })

    return JsonResponse({"error": "Invalid request"}, status=400)



@login_required
def admin_analytics(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Unauthorized access"}, status=403)

    total_scans = DocumentScan.objects.count()
    total_users = User.objects.count()
    top_users_by_scans = User.objects.annotate(scan_count=Count('documentscan')).order_by('-scan_count')[:5]
    top_users_by_credits = User.objects.annotate(credits_used=Sum('profile__credits')).order_by('profile__credits')[:5]
    daily_scans = DocumentScan.objects.extra(select={'day': 'date(scanned_at)'}).values('day').annotate(scan_count=Count('id')).order_by('-day')
    all_texts = DocumentScan.objects.values_list('content', flat=True)
    all_words = re.findall(r'\w+', ' '.join(all_texts).lower())
    common_topics = Counter(all_words).most_common(10)
    total_credits_requested = CreditRequest.objects.aggregate(Sum('requested_credits'))['requested_credits__sum'] or 0
    total_credits_approved = CreditRequest.objects.filter(approved=True).aggregate(Sum('requested_credits'))['requested_credits__sum'] or 0

    analytics_data = {
        "total_scans": total_scans,
        "total_users": total_users,
        "top_users_by_scans": [{"username": user.username, "scan_count": user.scan_count} for user in top_users_by_scans],
        "top_users_by_credits": [{"username": user.username, "credits_used": user.credits_used} for user in top_users_by_credits],
        "daily_scans": list(daily_scans),
        "common_topics": common_topics,
        "total_credits_requested": total_credits_requested,
        "total_credits_approved": total_credits_approved,
    }

    return render(request, "admin_analytics.html", {"analytics_data": analytics_data})



def get_matching_documents(document_text):
    """Compare scanned document with existing documents using BERT embeddings."""
    all_documents = DocumentScan.objects.all()
    documents_texts = [doc.content for doc in all_documents]

    if not documents_texts:
        return []

    query_embedding = model.encode(document_text, convert_to_tensor=True)
    document_embeddings = model.encode(documents_texts, convert_to_tensor=True)
    similarities = util.pytorch_cos_sim(query_embedding, document_embeddings)

    matching_docs = []
    for i, score in enumerate(similarities[0]):
        similarity_score = score.item()
        if similarity_score > 0.5:  # Adjust threshold as needed
            matching_docs.append({
                "document_id": all_documents[i].id,
                "document_name": all_documents[i].document_name,
                "similarity": round(similarity_score, 2)
            })

    return matching_docs


def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def credit_requests_list(request):
    credit_requests = CreditRequest.objects.filter(approved=False, denied=False)
    return render(request, 'admin/credit_requests_list.html', {'credit_requests': credit_requests})

@user_passes_test(is_admin)
def approve_credit_request(request, request_id):
    credit_request = CreditRequest.objects.get(id=request_id)
    credit_request.approved = True
    credit_request.save()
    credit_request.user.profile.credits += credit_request.requested_credits
    credit_request.user.profile.save()
    return redirect('credit_requests_list')

@user_passes_test(is_admin)
def deny_credit_request(request, request_id):
    credit_request = CreditRequest.objects.get(id=request_id)
    credit_request.denied = True
    credit_request.save()
    return redirect('credit_requests_list')