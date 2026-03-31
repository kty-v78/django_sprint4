from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Category, Comment
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator
from django.http import Http404
from django.utils import timezone

User = get_user_model()


def index(request):
    posts = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number=request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, id):
    post = get_object_or_404(Post, id=id)
    now = timezone.now()
    
    if (not post.is_published or 
        not post.category.is_published or 
        post.pub_date > now):
        if request.user != post.author:
            raise Http404("Пост не найден")
    
    comments = post.comments.all()
    form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category.objects.filter(is_published=True),
        slug=category_slug
    )

    posts = Post.objects.filter(
        is_published=True,
        category=category,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number=request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.author:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form, 'post': post})

def profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        posts = Post.objects.filter(author=user).order_by('-pub_date')
    else:
        posts = Post.objects.filter(
            author=user,
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number=request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    template_name = 'blog/user.html'
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})
    

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if (not post.is_published or 
        not post.category.is_published or 
        post.pub_date > timezone.now()):
        if request.user != post.author:
            return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    
    if request.user != comment.author:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment, 'post_id': post_id})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    
    if request.user != comment.author:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)
    
    return render(request, 'blog/comment.html', {'comment': comment, 'post_id': post_id})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.author:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    
    return render(request, 'blog/create.html', {'form': None, 'post': post})