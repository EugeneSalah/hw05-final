from http import HTTPStatus

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, UserEditForm, PostForm, ProfileEditForm
from .models import Comment, Follow, Group, Post, User, Profile


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, settings.PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {
        'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/group.html', {
        'group': group, 'page': page, 'paginator': paginator})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    profile_data = get_object_or_404(Profile, user=author)
    post_list = author.posts.all()
    paginator = Paginator(post_list, settings.PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and (
        Follow.objects.filter(user=request.user, author=author).exists())
    return render(request, 'posts/profile.html', {
        'author': author, 'following': following,
        'page': page, 'paginator': paginator, 'profile': True,
        'data': profile_data})


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related('author'),
                             id=post_id, author__username=username)
    comments = post.post_comments.all()
    form = CommentForm()
    return render(request, 'posts/post.html', {
        'author': post.author,
        'post': post,
        'form': form,
        'comments': comments})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'GET' or not form.is_valid():
        return render(request, 'posts/new_post.html',
                      {'form': form, 'mode': 'create'})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


@login_required
def post_edit(request, username, post_id):
    post_object = get_object_or_404(Post, id=post_id,
                                    author__username=username)
    if request.user != post_object.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post_object)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'posts/new_post.html', {
        'form': form, 'mode': 'edit', 'post': post_object})


def page404(request, exception=None):
    return render(request, 'misc/404.html', {'path': request.path},
                  status=HTTPStatus.NOT_FOUND)


def page500(request):
    return render(request, 'misc/500.html',
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.post_comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'posts/comments.html', {
        'form': form,
        'post': post,
        'author': post.author,
        'comments': comments})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {
        'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    follower = request.user
    following = get_object_or_404(User, username=username)
    if follower != following:
        Follow.objects.get_or_create(user=follower, author=following)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    follower = request.user
    following = get_object_or_404(User, username=username)
    Follow.objects.filter(user=follower, author=following).delete()
    return redirect('profile', username=username)


@login_required
def comment_delete(request, id):
    comment = get_object_or_404(Comment, id=id)
    if request.user == comment.author or request.user == comment.post.author:
        comment.delete()
    return redirect('post', username=comment.post.author,
                    post_id=comment.post.id)


@login_required
def post_delete(request, id):
    post = get_object_or_404(Post, id=id)
    if request.user == post.author:
        post.delete()
    return redirect('profile', username=post.author)


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(data=request.POST, instance=request.user)
        profile_form = ProfileEditForm(data=request.POST,
                                       instance=request.user.profile,
                                       files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile', username=request.user.username)
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request, 'posts/edit.html', {
        'user_form': user_form, 'profile_form': profile_form})
