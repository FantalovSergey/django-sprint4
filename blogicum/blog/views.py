from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count

from .models import Post, Category, Comment
from .forms import PostForm, UserUpdateForm, CommentForm


PAGINATE_BY = 10

User = get_user_model()


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        return self.get_object().author == self.request.user

    def handle_no_permission(self):
        if isinstance(self.get_object(), Post):
            return redirect(
                'blog:post_detail', pk=self.get_object().id)
        else:
            return redirect(
                'blog:post_detail', pk=self.get_object().post.id)


class PostMixin:
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username_slug': self.request.user})


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'pk': self.get_object().post.id})


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, PostMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'pk': self.get_object().id})


class PostDeleteView(OnlyAuthorMixin, PostMixin, DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class CommentUpdateView(OnlyAuthorMixin, CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(OnlyAuthorMixin, CommentMixin, DeleteView):
    pass


class UserUpdateView(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'

    def get_object(self):
        return get_object_or_404(User, username=self.request.user)

    def form_valid(self, form):
        self.success_url = reverse_lazy(
            'blog:profile', kwargs={'username_slug': form.instance.username})
        return super().form_valid(form)


def get_base_queryset():
    return Post.objects.select_related(
        'author', 'location', 'category',
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


def index(request):
    paginator = Paginator(get_base_queryset(), PAGINATE_BY)
    return render(
        request,
        'blog/index.html',
        {'page_obj': paginator.get_page(request.GET.get('page'))},
    )


def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related('author', 'location', 'category'),
        pk=pk,
    )
    if not post.author == request.user:
        post = get_object_or_404(get_base_queryset(), pk=pk)
    comments = Comment.objects.select_related('author').filter(
        post__id=pk)
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category.objects.filter(is_published=True), slug=category_slug)
    paginator = Paginator(
        get_base_queryset().filter(category__slug=category_slug), PAGINATE_BY)
    context = {
        'category': category,
        'page_obj': paginator.get_page(request.GET.get('page')),
    }
    return render(request, 'blog/category.html', context)


def profile(request, username_slug):
    user = get_object_or_404(User.objects.all(), username=username_slug)
    if user == request.user:
        paginator = Paginator(
            Post.objects.select_related(
                'author', 'location', 'category',
            ).filter(
                author__username=username_slug
            ).annotate(
                comment_count=Count('comments')
            ).order_by('-pub_date'),
            PAGINATE_BY,
        )
    else:
        paginator = Paginator(
            get_base_queryset().filter(author__username=username_slug),
            PAGINATE_BY,
        )
    context = {
        'profile': user,
        'page_obj': paginator.get_page(request.GET.get('page')),
    }
    return render(request, 'blog/profile.html', context)


@login_required
def add_comment(request, pk):
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=pk)
        comment.save()
    return redirect('blog:post_detail', pk=pk)
