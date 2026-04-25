from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Profile, Skill, UserSkill, SkillSwapRequest, ExchangeSession, Review,
    ProofArtifact, ChallengeSubmission, UserReport, ChatMessage, VerificationRequest, PeerChallenge
)


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'availability', 'location', 'avatar_url']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class UserSkillForm(forms.Form):
    skill_name = forms.CharField(max_length=80, label='Skill name')
    category = forms.ChoiceField(choices=Skill.CATEGORY_CHOICES)
    type = forms.ChoiceField(choices=UserSkill.SKILL_TYPE_CHOICES)
    level = forms.ChoiceField(choices=UserSkill.LEVEL_CHOICES)


class SkillSwapRequestForm(forms.ModelForm):
    class Meta:
        model = SkillSwapRequest
        fields = ['teach_skill', 'learn_skill', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explain what you can teach and what you want to learn.'}),
        }

    def __init__(self, *args, sender=None, receiver=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sender and receiver:
            self.fields['teach_skill'].queryset = Skill.objects.filter(
                user_skills__user=sender,
                user_skills__type=UserSkill.HAVE,
            ).distinct()
            self.fields['learn_skill'].queryset = Skill.objects.filter(
                user_skills__user=receiver,
                user_skills__type=UserSkill.HAVE,
            ).distinct()


class ExchangeSessionForm(forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = ExchangeSession
        fields = ['scheduled_at', 'duration_minutes', 'session_notes', 'mini_assignment', 'learner_reflection']
        widgets = {
            'session_notes': forms.Textarea(attrs={'rows': 3}),
            'mini_assignment': forms.Textarea(attrs={'rows': 3}),
            'learner_reflection': forms.Textarea(attrs={'rows': 3}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }


class ProofArtifactForm(forms.ModelForm):
    class Meta:
        model = ProofArtifact
        fields = ['title', 'description', 'link']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class ChallengeSubmissionForm(forms.ModelForm):
    class Meta:
        model = ChallengeSubmission
        fields = ['title', 'link', 'reflection']
        widgets = {'reflection': forms.Textarea(attrs={'rows': 4})}


class UserReportForm(forms.ModelForm):
    class Meta:
        model = UserReport
        fields = ['reason', 'details']
        widgets = {'details': forms.Textarea(attrs={'rows': 4})}


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Write a session message, update, question, or next step...'
            })
        }


class VerificationRequestForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ['headline', 'proof_links', 'motivation']
        widgets = {
            'proof_links': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Paste portfolio, LinkedIn, GitHub, certificate, or project links.'}),
            'motivation': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explain your skill background and why peers can trust your profile.'}),
        }


class PeerChallengeCreateForm(forms.ModelForm):
    due_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        label='Due date / time',
    )

    class Meta:
        model = PeerChallenge
        fields = ['mode', 'title', 'description', 'skill_focus', 'due_at']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Example: Build a simple portfolio page and share the link with a short reflection.'
            }),
            'title': forms.TextInput(attrs={'placeholder': 'Example: Build a one-page portfolio'}),
            'skill_focus': forms.TextInput(attrs={'placeholder': 'Example: HTML, CSS, UI design'}),
        }


class PeerChallengeProofForm(forms.Form):
    proof_title = forms.CharField(max_length=140, label='Proof title')
    proof_file = forms.FileField(
        required=True,
        label='Upload proof file',
        help_text='Upload any proof file: image, PDF, ZIP, .py, .html, .docx, etc.',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.png,.jpg,.jpeg,.gif,.webp,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.py,.ipynb,.html,.css,.js,.zip,.rar,.mp4,.mov'
        })
    )
    reflection = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'What did you build, learn, or improve?'}),
        required=False,
    )

    def clean_proof_file(self):
        proof_file = self.cleaned_data.get('proof_file')
        if proof_file and proof_file.size > 25 * 1024 * 1024:
            raise forms.ValidationError('File is too large. Maximum allowed size is 25 MB.')
        return proof_file
