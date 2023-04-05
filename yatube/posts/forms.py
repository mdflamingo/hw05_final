from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Tекст поста',
            'group': 'Группа',
        }
        help_texts = {'text': 'Введите текст',
                      'group': 'Выберите группу из списка'
                      }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
