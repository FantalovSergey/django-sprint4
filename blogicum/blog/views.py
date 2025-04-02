from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from .models import Category, Post
from .forms import CommentForm, PostForm, UserUpdateForm
from .mixins import CommentMixin, OnlyAuthorMixin, PostMixin
from .utils import get_base_queryset, get_page

User = get_user_model()


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, PostMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.get_object().id})


class PostDeleteView(OnlyAuthorMixin, PostMixin, DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class CommentUpdateView(OnlyAuthorMixin, CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(OnlyAuthorMixin, CommentMixin, DeleteView):
    pass


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username_slug': self.get_object().username},
        )


def index(request):
    page = get_page(request, get_base_queryset(filter=True, annotate=True))
    return render(request, 'blog/index.html', {'page_obj': page})


def post_detail(request, post_id):
    post = get_object_or_404(get_base_queryset(), pk=post_id)
    if not post.author == request.user:
        post = get_object_or_404(
            get_base_queryset(filter=True, annotate=True), pk=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category.objects.filter(is_published=True), slug=category_slug)
    page = get_page(
        request,
        get_base_queryset(
            filter=True, annotate=True,
        ).filter(category__slug=category_slug),
    )
    context = {
        'category': category,
        'page_obj': page,
    }
    return render(request, 'blog/category.html', context)


def profile(request, username_slug):
    user = get_object_or_404(User, username=username_slug)
    if user == request.user:
        queryset = get_base_queryset(annotate=True).filter(
            author__username=username_slug)
    else:
        queryset = get_base_queryset(filter=True, annotate=True).filter(
            author__username=username_slug)
    context = {
        'profile': user,
        'page_obj': get_page(request, queryset),
    }
    return render(request, 'blog/profile.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)
