from django.db import migrations, models


WEATHER_WIDGET_SLUG = 'weather-widget'
WEATHER_WIDGET_VERSION = '1.0.0'
WEATHER_MANIFEST = {'name': 'Weather Widget', 'slug': 'weather-widget', 'version': '1.0.0', 'kind': 'embed', 'placements': ['homepage_top', 'homepage_bottom'], 'configSchema': {'type': 'object', 'properties': {'defaultLocation': {'type': 'string'}, 'unit': {'type': 'string', 'enum': ['C', 'F']}, 'locale': {'type': 'string'}, 'forecastDays': {'type': 'integer', 'minimum': 1, 'maximum': 7}}}, 'permissions': {'network': ['wttr.in'], 'projectDataRead': False, 'projectDataWrite': False, 'usesSecrets': False}}
WEATHER_CONFIG_SCHEMA = {'type': 'object', 'properties': {'defaultLocation': {'type': 'string'}, 'unit': {'type': 'string', 'enum': ['C', 'F']}, 'locale': {'type': 'string'}, 'forecastDays': {'type': 'integer', 'minimum': 1, 'maximum': 7}}}
WEATHER_PERMISSIONS = {'network': ['wttr.in'], 'projectDataRead': False, 'projectDataWrite': False, 'usesSecrets': False}
WEATHER_SOURCE_HTML = '<section class="weather-card" data-weather-widget>\n  <div class="weather-head">\n    <div>\n      <span class="eyebrow">External API demo</span>\n      <h2>Weather widget</h2>\n      <p class="subtitle weather-subtitle">Live wttr.in weather makes the external API call visible through the approved widget framework.</p>\n    </div>\n    <form class="weather-form" data-weather-form>\n      <input type="text" name="location" aria-label="Weather location" placeholder="Enter a city or place">\n      <button type="submit" class="button secondary">Check weather</button>\n    </form>\n  </div>\n  <div class="weather-settings">\n    <div class="weather-setting">\n      <span class="weather-setting-label">Units</span>\n      <div class="weather-toggle" role="group" aria-label="Temperature units">\n        <button type="button" class="weather-toggle-button" data-unit-toggle="C">°C</button>\n        <button type="button" class="weather-toggle-button" data-unit-toggle="F">°F</button>\n      </div>\n    </div>\n    <label class="weather-setting weather-locale-setting">\n      <span class="weather-setting-label">Localization</span>\n      <input type="text" name="locale" data-weather-locale aria-label="Weather localization" placeholder="Locale code (en, fr, es)">\n    </label>\n  </div>\n  <div class="weather-output" data-weather-output>\n    <p class="weather-status">Loading weather…</p>\n  </div>\n</section>'
WEATHER_SOURCE_CSS = '.weather-card {\n  padding: 24px;\n  border-radius: 20px;\n  border: 1px solid rgba(148,163,184,0.16);\n  background: #0d1728;\n}\n.weather-head {\n  display: flex;\n  align-items: end;\n  justify-content: space-between;\n  gap: 18px;\n  flex-wrap: wrap;\n}\n.weather-head h2 {\n  margin: 10px 0 8px;\n  letter-spacing: -0.03em;\n}\n.weather-subtitle {\n  margin: 0;\n}\n.weather-form,\n.weather-settings {\n  display: flex;\n  gap: 10px;\n  flex-wrap: wrap;\n}\n.weather-settings {\n  margin-top: 14px;\n  align-items: end;\n}\n.weather-setting {\n  display: grid;\n  gap: 8px;\n}\n.weather-setting-label,\n.weather-label {\n  color: #8fb8ff;\n  font-size: 0.78rem;\n  font-weight: 800;\n  text-transform: uppercase;\n  letter-spacing: 0.08em;\n}\n.weather-form input,\n.weather-setting input {\n  min-width: 220px;\n  padding: 12px 14px;\n  border-radius: 14px;\n  border: 1px solid rgba(148,163,184,0.18);\n  background: #07111f;\n  color: #ecf3ff;\n}\n.weather-toggle {\n  display: inline-flex;\n  gap: 8px;\n}\n.weather-toggle-button {\n  min-width: 72px;\n  padding: 12px 14px;\n  border-radius: 14px;\n  border: 1px solid rgba(148,163,184,0.18);\n  background: #07111f;\n  color: #9fb0ca;\n  font-weight: 800;\n  cursor: pointer;\n}\n.weather-toggle-button.is-active {\n  background: linear-gradient(135deg, #5ea3ff, #7c5cff);\n  color: #fff;\n  border-color: transparent;\n}\n.weather-output,\n.weather-forecast {\n  margin-top: 18px;\n}\n.weather-forecast-header {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: 10px;\n  flex-wrap: wrap;\n  margin-bottom: 12px;\n}\n.weather-grid,\n.weather-forecast-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));\n  gap: 12px;\n}\n.weather-metric,\n.weather-forecast-card {\n  padding: 16px;\n  border-radius: 16px;\n  border: 1px solid rgba(148,163,184,0.14);\n  background: rgba(21,36,58,0.58);\n}\n.weather-forecast-card {\n  background: rgba(21,36,58,0.42);\n}\n.weather-summary {\n  grid-column: span 2;\n}\n.weather-metric strong,\n.weather-forecast-card strong {\n  display: block;\n  font-size: 1.3rem;\n  margin-bottom: 6px;\n}\n.weather-metric p,\n.weather-status,\n.weather-meta,\n.weather-forecast-card p {\n  margin: 0;\n  color: #9fb0ca;\n  line-height: 1.6;\n}\n.weather-error {\n  color: #ffb4b4;\n}\n@media (max-width: 640px) {\n  .weather-summary {\n    grid-column: auto;\n  }\n  .weather-form,\n  .weather-form input,\n  .weather-form button,\n  .weather-settings,\n  .weather-setting,\n  .weather-setting input,\n  .weather-toggle,\n  .weather-toggle-button {\n    width: 100%;\n  }\n}'
WEATHER_SOURCE_JS = 'const widget = root.querySelector(\'[data-weather-widget]\');\nif (!widget) return;\nconst form = widget.querySelector(\'[data-weather-form]\');\nconst input = form?.querySelector(\'input[name="location"]\');\nconst localeInput = widget.querySelector(\'[data-weather-locale]\');\nconst unitButtons = [...widget.querySelectorAll(\'[data-unit-toggle]\')];\nconst output = widget.querySelector(\'[data-weather-output]\');\nif (!form || !input || !output) return;\n\nconst escapeHtml = (value) => String(value ?? \'\')\n  .replace(/&/g, \'&amp;\')\n  .replace(/</g, \'&lt;\')\n  .replace(/>/g, \'&gt;\')\n  .replace(/"/g, \'&quot;\')\n  .replace(/\'/g, \'&#39;\');\n\nconst state = {\n  unit: String(config.unit || \'C\').toUpperCase() === \'F\' ? \'F\' : \'C\',\n  locale: String(config.locale || \'en\').trim().toLowerCase() || \'en\',\n  forecastDays: Math.min(Math.max(parseInt(config.forecastDays || 3, 10) || 3, 1), 7),\n  lastLocation: String(config.defaultLocation || project.name || \'New York\').trim(),\n  lastData: null,\n};\n\ninput.value = state.lastLocation;\nif (localeInput) localeInput.value = state.locale;\n\nconst unitMeta = {\n  C: { degree: \'°C\', speedUnit: \'km/h\', rainUnit: \'mm\', tempKey: \'temp_C\', feelsKey: \'FeelsLikeC\', maxKey: \'maxtempC\', minKey: \'mintempC\', avgKey: \'avgtempC\', speedKey: \'windspeedKmph\', rainKey: \'precipMM\' },\n  F: { degree: \'°F\', speedUnit: \'mph\', rainUnit: \'in\', tempKey: \'temp_F\', feelsKey: \'FeelsLikeF\', maxKey: \'maxtempF\', minKey: \'mintempF\', avgKey: \'avgtempF\', speedKey: \'windspeedMiles\', rainKey: \'precipInches\' },\n};\n\nfunction syncUnitButtons() {\n  unitButtons.forEach((button) => {\n    const isActive = button.dataset.unitToggle === state.unit;\n    button.classList.toggle(\'is-active\', isActive);\n    button.setAttribute(\'aria-pressed\', isActive ? \'true\' : \'false\');\n  });\n}\n\nfunction renderWeather(data) {\n  const current = data?.current_condition?.[0] || {};\n  const today = data?.weather?.[0] || {};\n  const nearest = data?.nearest_area?.[0] || {};\n  const unit = unitMeta[state.unit] || unitMeta.C;\n  const area = nearest?.areaName?.[0]?.value || state.lastLocation;\n  const region = nearest?.region?.[0]?.value || \'\';\n  const country = nearest?.country?.[0]?.value || \'\';\n  const label = [area, region, country].filter(Boolean).join(\', \');\n  const description = current?.weatherDesc?.[0]?.value || \'Unknown conditions\';\n  const forecast = (data?.weather || []).slice(0, state.forecastDays).map((day) => {\n    const forecastText = day?.hourly?.[4]?.weatherDesc?.[0]?.value || day?.hourly?.[0]?.weatherDesc?.[0]?.value || \'Forecast unavailable\';\n    return `\n      <article class="weather-forecast-card">\n        <span class="weather-label">${escapeHtml(day.date || \'Upcoming\')}</span>\n        <strong>${escapeHtml(day[unit.maxKey] || \'–\')}${escapeHtml(unit.degree)} / ${escapeHtml(day[unit.minKey] || \'–\')}${escapeHtml(unit.degree)}</strong>\n        <p>${escapeHtml(forecastText)}</p>\n        <p class="weather-meta">Avg ${escapeHtml(day[unit.avgKey] || \'–\')}${escapeHtml(unit.degree)}</p>\n      </article>\n    `;\n  }).join(\'\');\n  output.innerHTML = `\n    <div class="weather-grid">\n      <div class="weather-metric weather-summary">\n        <span class="weather-label">Location</span>\n        <strong>${escapeHtml(label)}</strong>\n        <p>${escapeHtml(description)}</p>\n        <p class="weather-meta">Locale ${escapeHtml(state.locale)} · Units ${escapeHtml(unit.degree)} · Forecast ${escapeHtml(state.forecastDays)} day(s)</p>\n      </div>\n      <div class="weather-metric">\n        <span class="weather-label">Temp</span>\n        <strong>${escapeHtml(current[unit.tempKey] || \'–\')}${escapeHtml(unit.degree)}</strong>\n        <p>Feels like ${escapeHtml(current[unit.feelsKey] || \'–\')}${escapeHtml(unit.degree)}</p>\n      </div>\n      <div class="weather-metric">\n        <span class="weather-label">Wind</span>\n        <strong>${escapeHtml(current[unit.speedKey] || \'–\')} ${escapeHtml(unit.speedUnit)}</strong>\n        <p>${escapeHtml(current.winddir16Point || \'\')}</p>\n      </div>\n      <div class="weather-metric">\n        <span class="weather-label">Humidity</span>\n        <strong>${escapeHtml(current.humidity || \'–\')}%</strong>\n        <p>Rain ${escapeHtml(current[unit.rainKey] || \'0\')} ${escapeHtml(unit.rainUnit)}</p>\n      </div>\n      <div class="weather-metric">\n        <span class="weather-label">Today</span>\n        <strong>${escapeHtml(today[unit.maxKey] || \'–\')}${escapeHtml(unit.degree)} / ${escapeHtml(today[unit.minKey] || \'–\')}${escapeHtml(unit.degree)}</strong>\n        <p>Avg ${escapeHtml(today[unit.avgKey] || \'–\')}${escapeHtml(unit.degree)}</p>\n      </div>\n    </div>\n    <div class="weather-forecast">\n      <div class="weather-forecast-header">\n        <span class="weather-label">Forecast</span>\n        <p class="weather-meta">Showing the next ${escapeHtml(state.forecastDays)} day(s)</p>\n      </div>\n      <div class="weather-forecast-grid">${forecast}</div>\n    </div>\n  `;\n}\n\nasync function loadWeather(location) {\n  const cleanLocation = (location || state.lastLocation || project.name || \'New York\').trim();\n  state.lastLocation = cleanLocation;\n  if (localeInput) {\n    state.locale = (localeInput.value || state.locale || \'en\').trim().toLowerCase() || \'en\';\n    localeInput.value = state.locale;\n  }\n  output.innerHTML = \'<p class="weather-status">Loading weather…</p>\';\n  try {\n    const response = await fetch(`https://wttr.in/${encodeURIComponent(cleanLocation)}?format=j1&lang=${encodeURIComponent(state.locale)}`, {\n      headers: { Accept: \'application/json\' },\n    });\n    if (!response.ok) throw new Error(`Weather lookup failed (${response.status})`);\n    state.lastData = await response.json();\n    renderWeather(state.lastData);\n  } catch (error) {\n    output.innerHTML = `<p class="weather-status weather-error">Could not load weather for ${escapeHtml(cleanLocation)}. ${escapeHtml(error.message || \'Try again in a moment.\')}</p>`;\n  }\n}\n\nform.addEventListener(\'submit\', (event) => {\n  event.preventDefault();\n  loadWeather(input.value);\n});\n\nif (localeInput) localeInput.addEventListener(\'change\', () => loadWeather(input.value));\nunitButtons.forEach((button) => {\n  button.addEventListener(\'click\', () => {\n    state.unit = button.dataset.unitToggle === \'F\' ? \'F\' : \'C\';\n    syncUnitButtons();\n    if (state.lastData) renderWeather(state.lastData);\n  });\n});\n\nsyncUnitButtons();\nloadWeather(input.value);'


def seed_weather_widget(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    WidgetDefinition = apps.get_model('projects', 'WidgetDefinition')
    WidgetVersion = apps.get_model('projects', 'WidgetVersion')
    WidgetInstallation = apps.get_model('projects', 'WidgetInstallation')

    widget, _ = WidgetDefinition.objects.get_or_create(
        slug=WEATHER_WIDGET_SLUG,
        defaults={
            'name': 'Weather Widget',
            'description': 'Approved external API weather widget powered by wttr.in.',
            'category': 'external-api',
            'is_system': True,
            'status': 'approved',
            'visibility': 'shared',
        },
    )
    widget.name = 'Weather Widget'
    widget.description = 'Approved external API weather widget powered by wttr.in.'
    widget.category = 'external-api'
    widget.is_system = True
    widget.status = 'approved'
    widget.visibility = 'shared'
    widget.save(update_fields=['name', 'description', 'category', 'is_system', 'status', 'visibility', 'updated_at'])

    version, _ = WidgetVersion.objects.get_or_create(
        widget=widget,
        version=WEATHER_WIDGET_VERSION,
        defaults={
            'manifest_json': WEATHER_MANIFEST,
            'config_schema_json': WEATHER_CONFIG_SCHEMA,
            'permissions_json': WEATHER_PERMISSIONS,
            'source_html': WEATHER_SOURCE_HTML,
            'source_css': WEATHER_SOURCE_CSS,
            'source_js': WEATHER_SOURCE_JS,
            'review_status': 'approved',
            'review_notes': 'Built-in approved weather widget.',
        },
    )
    version.manifest_json = WEATHER_MANIFEST
    version.config_schema_json = WEATHER_CONFIG_SCHEMA
    version.permissions_json = WEATHER_PERMISSIONS
    version.source_html = WEATHER_SOURCE_HTML
    version.source_css = WEATHER_SOURCE_CSS
    version.source_js = WEATHER_SOURCE_JS
    version.review_status = 'approved'
    version.review_notes = 'Built-in approved weather widget.'
    version.save(update_fields=['manifest_json', 'config_schema_json', 'permissions_json', 'source_html', 'source_css', 'source_js', 'review_status', 'review_notes'])

    if widget.current_approved_version_id != version.id:
        widget.current_approved_version = version
        widget.save(update_fields=['current_approved_version', 'updated_at'])

    for project in Project.objects.all():
        should_install = project.framework == 'html' or (project.framework == 'django' and project.starter_theme == 'list_manager')
        if not should_install:
            continue
        WidgetInstallation.objects.get_or_create(
            project=project,
            widget=widget,
            defaults={
                'widget_version': version,
                'placement': 'homepage_bottom',
                'title_override': 'Live weather',
                'config_json': {'defaultLocation': 'New York', 'unit': 'C', 'locale': 'en', 'forecastDays': 3},
                'sort_order': 100,
                'is_enabled': True,
            },
        )


def unseed_weather_widget(apps, schema_editor):
    WidgetDefinition = apps.get_model('projects', 'WidgetDefinition')
    WidgetDefinition.objects.filter(slug=WEATHER_WIDGET_SLUG, is_system=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_widgetdefinition_widgetversion_widgetreviewevent_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='widgetdefinition',
            name='is_system',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_weather_widget, unseed_weather_widget),
    ]
