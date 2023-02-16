from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Comment, Group, Follow, Post, User


SYMBOLS_FOR_TITLE = 100


def paginator(request, post_list):
    func_paginator = Paginator(post_list, settings.AMOUNT_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = func_paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница."""
    post_list = Post.objects.all()
    page_obj = paginator(request, post_list)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    """Страница сообщества."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group', 'author').all()
    page_obj = paginator(request, post_list)
    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': page_obj},
    )


def profile(request, username):
    """Профиль пользователя."""
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    count = posts.count()
    paginator = Paginator(posts, settings.AMOUNT_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'count': count,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница конкретного поста."""
    post = get_object_or_404(Post, pk=post_id)
    comment = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'form': form,
        'comment': comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создает новый пост."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    """Редактирует существующий пост."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Добавляет комментарий."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Информация о текущем пользователе доступна в переменной request.user"""
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
        'follow': True
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора"""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('posts:profile', username)
