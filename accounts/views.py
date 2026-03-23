from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import UserProfile


def login_view(request):
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dash_home")
        else:
            error = "Invalid username or password."
    return render(request, "accounts/login.html", {"error": error})


def register_view(request):
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        role = request.POST.get("role", "farmer")

        if User.objects.filter(username=username).exists():
            error = "Username already exists."
        elif len(password) < 4:
            error = "Password too short (min 4 chars)."
        else:
            user = User.objects.create_user(username=username, password=password)
            UserProfile.objects.create(user=user, role=role)
            login(request, user)
            return redirect("dash_home")

    return render(request, "accounts/register.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")