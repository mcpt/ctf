from django.core.exceptions import ValidationError
from django.db import models

from gameserver.models import ContestParticipation


def validate_coordinates(value):
    try:
        _, _ = map(int, value.split(","))
    except ValueError:
        raise ValidationError("Invalid coordinates format. Must be 'x,y'.")


class CoordinatesField(models.CharField):
    default_validators = [validate_coordinates]


class Certificate(models.Model):
    template = models.ImageField(
        upload_to="certificates/",
        help_text="The certificate template image. It must be a JPG file and if you're unsure about anything, please refer to the documentation or contact a site admin.",
    )
    contest = models.OneToOneField(
        "Contest",
        on_delete=models.CASCADE,
        related_name="certificate",
        help_text="The contest this certificate is for.",
    )

    name_start = CoordinatesField(help_text="The coordinates where the name should start.")
    name_end = CoordinatesField(help_text="The coordinates where the name should end.")

    name_font_size = models.PositiveSmallIntegerField(help_text="The font size for the name.")

    font_file = models.FileField(
        upload_to="fonts/",
        help_text="The font file to use for the name. It must be a TTF file. If left blank the system's default font will be used.",
        blank=True,
        null=True,
    )

    points_start = CoordinatesField(
        help_text="The coordinates where the point count should start. NOTE: Leave blank if you don't want to display the points."
    )
    points_end = CoordinatesField(
        help_text="The coordinates where the point count should end. NOTE: Leave blank if you don't want to display the points."
    )

    points_font_size = models.PositiveSmallIntegerField(
        help_text="The font size for the points. NOTE: Leave blank if you don't want to display the points."
    )

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"

        constraints = [
            models.CheckConstraint(
                name="all_points_fields_or_none",
                check=models.Q(
                    points_start__isnull=True,
                    points_end__isnull=True,
                    points_font_size__isnull=True,
                )
                | models.Q(
                    points_start__isnull=False,
                    points_end__isnull=False,
                    points_font_size__isnull=False,
                ),
            ),
            models.CheckConstraint(
                name="all_name_fields_or_none",
                check=models.Q(
                    name_start__isnull=True,
                    name_end__isnull=True,
                    name_font_size__isnull=True,
                )
                | models.Q(
                    name_start__isnull=False,
                    name_end__isnull=False,
                    name_font_size__isnull=False,
                ),
            ),
        ]
        
    def generate_certificate(self, participant: ContestParticipation):
        # Generate the certificate image
        # This is a placeholder function and will be implemented later
        pass
