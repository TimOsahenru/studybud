from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from .forms import *
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


# ........................ All rooms .................................
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q) |
                                Q(host__username__icontains=q))
    room_count = rooms.count()
    topics = Topic.objects.all()
    room_message = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count, 'room_message': room_message}
    return render(request, 'home.html', context)


# ........................ Detailed Room .................................
def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == 'POST':
        #  Creating the actual message for each room
        #  For the user variable we use the requested user
        #  For the room variable we use the current room
        #  For the body variable we get it from our front-end

        message = Message.objects.create(user=request.user, room=room, body=request.POST.get('body'))
        # Once a user comment/message they are been added as participants of that room
        room.participants.add(request.user)

        #  We add this line of code to allow the message creation process load fully
        #  this can be achieved without this line of code but might face some errors later
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'room.html', context)


# ........................ Create room .................................
@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'room_form.html', context)


# ........................ Update room .................................
@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)

    if request.user != room.host:
        return HttpResponse('You are not allowed here')

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'room_form.html', context)


# ........................ Delete views .................................
@login_required(login_url='login')
def delete(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'delete.html', {'obj': room})


# ........................ Login views .................................
def login_page(request):

    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username, password=password)
        except:
            messages.error(request, 'Invalid login credentials')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        # else:
        #     messages.error(request, 'Invalid login credentials')

    context = {'page': page}
    return render(request, 'login_register.html', context)


# ........................ Logout views .................................
def logout_user(request):
    logout(request)
    return redirect('home')


def register_user(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Error signing in, try again')
            return redirect('register')

    context = {'form': form}
    return render(request, 'login_register.html', context)


# ........................ Delete message views .................................
@login_required(login_url='login')
def delete_message(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed here')

    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=message.room.id)
    return render(request, 'delete.html', {'obj': message})


# ........................ Edit message views .................................
# def edit_message(request, pk):
#     message = Message.objects.get(id=pk)
#
#     if request.user != message.owner:
#         return HttpResponse('You are not allowed here')
#
#     if request.method == 'POST':
#         message_update = (request.POST, instance=message)


# ........................ Profile views .................................
def profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_message = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_message': room_message, 'topics': topics}
    return render(request, 'profile.html', context)
