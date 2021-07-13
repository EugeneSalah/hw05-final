from django import forms

from .models import Comment, Post, User, Profile


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {'text': 'Введите текст записи',
                      'group': 'Выберите группу',
                      'image': 'Загрузите изображение'}
        labels = {'text': 'Текст', 'group': 'Группа', 'image': 'изображение'}
        widgets = {'text': forms.Textarea()}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('date_of_birth', 'photo')
