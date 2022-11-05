from django.shortcuts import (
    render, get_object_or_404, redirect
)

from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Comment, Follow

from .forms import PostForm, CommentForm


POSTS_PER_PAGE = 10


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts_list = Post.objects.filter(author=author)
    paginator = Paginator(posts_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    posts_count = posts_list.count()
    following = False
    if request.user.id:
        following = Follow.objects.filter(
            author=author, user=request.user
        ).exists()
    context = {
        'posts_list': posts_list,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = Post.objects.get(pk=post_id)
    posts_count = Post.objects.filter(author=post.author).count()
    user_posts_link = 'profile/' + post.author.username
    is_authenticated = False
    if request.user.username:
        is_authenticated = True
    is_author = False
    if post.author == request.user:
        is_author = True
    comment_form = CommentForm()
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'posts_count': posts_count,
        'user_posts_link': user_posts_link,
        'post_id': post_id,
        'is_authenticated': is_authenticated,
        'is_author': is_author,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    template = 'posts/create_post.html'
    context = {
        'form': form
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
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
    post_list = Post.objects.none()
    if Follow.objects.filter(user=request.user).exists():
        subscriptions = Follow.objects.filter(user=request.user)
        for subscription in subscriptions:
            post_list = post_list | Post.objects.filter(
                author=subscription.author
            )
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.filter(username=username)[0]
    if not Follow.objects.filter(
        user=request.user, author=author).exists() and author != request.user:
            Follow.objects.create(
                user=request.user, author=author
            )
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = User.objects.filter(username=username)[0]
    if Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', author)
