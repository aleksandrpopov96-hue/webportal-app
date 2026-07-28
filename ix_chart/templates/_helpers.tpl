{{/*
Common labels
*/}}
{{- define "webportal.labels" -}}
app: {{ .Chart.Name }}
chart: {{ .Chart.Name }}-{{ .Chart.Version }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "webportal.selectorLabels" -}}
app: {{ .Release.Name }}
{{- end }}
