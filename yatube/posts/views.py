from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm
from .utils import get_page_context


def index(request):
    """Выводит шаблон главной страницы."""
    context = get_page_context(request, Post.objects.all())

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Выводит шаблон с группами постов"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(get_page_context(request, group.posts.all()))

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профайла пользователя"""
    author = get_object_or_404(User, username=username)
    context = {
        'author': author,
    }
    context.update(get_page_context(request, author.posts.all()))

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Выводит шаблон страницы поста."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()

    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()

    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'posts/post_detail.html', context, post_id)


@login_required
def add_comment(request, post_id):
    """Обрабатывает создания поста."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    """Выводит шаблон создания поста."""
    form_post = PostForm(request.POST or None)
    if form_post.is_valid():
        form_post = form_post.save(commit=False)
        form_post.author = request.user
        form_post.save()

        return redirect('posts:profile', request.user.username)
    context = {
        'form': form_post,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Выводит шаблон редактирования поста."""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:

        return redirect('posts:post_detail', post_id=post.id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()

        return redirect('posts:post_detail', post_id=post.id)

    context = {
        'form': form,
        'is_edit': True,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def follow_index(request):
    posts_list = Post.objects.filter(author__following__user=request.user)
    page_context = get_page_context(request, posts_list)

    return render(request, 'posts/follow.html', page_context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.filter(user=user, author__username=username).delete()
    return redirect('posts:profile', username=username)

