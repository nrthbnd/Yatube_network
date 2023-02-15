from django.contrib.auth.views import (PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ChangeForm, CreationForm, ResetForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class ChangeForm(PasswordChangeView):
    form_class = ChangeForm
    template_name = 'users/password_change_form.html'
    success_url = reverse_lazy('users:password_change_done')


class ChangeDoneForm(PasswordChangeDoneView):
    form_class = ChangeForm
    template_name = 'users/password_change_done.html'


class ResetForm(PasswordResetView):
    form_class = ResetForm
    template_name = 'users/password_reset_form.html'
    success_url = reverse_lazy('users:password_reset_done')


class ResetDoneForm(PasswordResetDoneView):
    form_class = ResetForm
    template_name = 'users/password_reset_done.html'
    success_url = reverse_lazy('users:password_reset_confirm')


class ResetConfirmForm(PasswordResetConfirmView):
    form_class = ResetForm
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')


class ResetCompleteForm(PasswordResetCompleteView):
    form_class = ResetForm
    template_name = 'users/password_reset_complete.html'
