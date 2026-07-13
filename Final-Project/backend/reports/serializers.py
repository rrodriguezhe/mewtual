from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["usuario_reportante"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if not (request and request.user.is_staff):
            fields["estado"].read_only = True
        return fields

    def validate(self, data):
        request = self.context.get("request")
        if request and data.get("usuario_reportado") == request.user:
            raise serializers.ValidationError(
                "No puedes reportarte a ti mismo."
            )
        return data
