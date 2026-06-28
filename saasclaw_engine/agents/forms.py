from django import forms


MODE_CHOICES = [
    ('edit', 'Edit app'),
    ('plan', 'Planner'),
    ('resource', 'Create resource'),
    ('resource_edit', 'Edit resource'),
]


FIELD_TYPE_CHOICES = [
    ('text', 'Text'),
    ('textarea', 'Long text'),
    ('email', 'Email'),
    ('integer', 'Integer'),
    ('decimal', 'Decimal (2 places)'),
    ('boolean', 'Boolean'),
    ('date', 'Date'),
]


class ProjectAiEditForm(forms.Form):
    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        initial='edit',
        required=False,
        widget=forms.RadioSelect,
        help_text='Use Planner for non-mutating conversation, Edit app for safe UI changes, and the resource lanes for structured Django CRUD work.',
    )
    prompt = forms.CharField(
        label='What should SaaSClaw do?',
        widget=forms.Textarea(attrs={'rows': 10, 'placeholder': 'Example: Plan a cleaner pricing page with a stronger hero, FAQ, and CTA hierarchy. Or switch to Edit app mode and ask for a safer template/UI change.'}),
        help_text='Describe the plan or edit you want. Planner will respond without changing files. Edit app can update templates, styling, and limited app logic without touching models or core app structure.',
    )
    image = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        help_text='Optional reference image for design direction or UI feedback.',
    )
    auto_deploy_preview = forms.BooleanField(required=False, initial=True)

    def clean_image(self):
        uploaded = self.cleaned_data.get('image')
        if not uploaded:
            return uploaded
        content_type = (getattr(uploaded, 'content_type', '') or '').lower()
        if content_type and not content_type.startswith('image/'):
            raise forms.ValidationError('Upload an image file.')
        return uploaded


class ProjectCreateResourceForm(forms.Form):
    resource_name = forms.CharField(
        label='Resource name',
        max_length=80,
        widget=forms.TextInput(attrs={'placeholder': 'Employee'}),
        help_text='Use a singular name like Employee, Customer, or Order.',
    )
    description = forms.CharField(
        required=False,
        label='Description',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional: track employees and their contact info, department, and hire date.'}),
        help_text='Optional extra context for better field suggestions.',
    )
    fields_text = forms.CharField(
        label='Fields',
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'name:text\nemail:email\naddress:textarea'}),
        help_text='One field per line in the format name:type. Supported types: text, textarea, email, integer, decimal, boolean, date.',
    )
    include_admin = forms.BooleanField(required=False, initial=True)
    include_crud = forms.BooleanField(required=False, initial=True)
    add_nav_link = forms.BooleanField(required=False, initial=True)

    def clean_fields_text(self):
        value = (self.cleaned_data.get('fields_text') or '').strip()
        if not value:
            raise forms.ValidationError('Add at least one field.')
        parsed = []
        seen = set()
        for raw_line in value.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if ':' not in line:
                raise forms.ValidationError(f'Invalid field format: {line}. Use name:type.')
            name, field_type = [part.strip().lower() for part in line.split(':', 1)]
            if not name or not field_type:
                raise forms.ValidationError(f'Invalid field format: {line}. Use name:type.')
            field_type = {
                'int': 'integer',
                'number': 'decimal',
                'float': 'decimal',
                'money': 'decimal',
                'currency': 'decimal',
            }.get(field_type, field_type)
            allowed_types = {choice[0] for choice in FIELD_TYPE_CHOICES}
            if field_type not in allowed_types:
                raise forms.ValidationError(f'Unsupported field type for {name}: {field_type}.')
            if name in seen:
                raise forms.ValidationError(f'Duplicate field name: {name}.')
            seen.add(name)
            parsed.append({'name': name, 'type': field_type})
        if not parsed:
            raise forms.ValidationError('Add at least one field.')
        self.cleaned_data['parsed_fields'] = parsed
        return value
