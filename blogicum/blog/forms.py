from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ['is_published', 'author']
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%d %H:%M',
                attrs={'type': 'datetime-local', 'max': '9999-12-31 23:59'},
            )
        }


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
