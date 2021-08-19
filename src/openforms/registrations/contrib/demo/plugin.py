from typing import NoReturn, Tuple

from django.utils.translation import ugettext_lazy as _

from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...exceptions import RegistrationFailed
from ...registry import register
from .config import DemoOptionsSerializer


@register("demo")
class DemoRegistration(BasePlugin):
    verbose_name = _("Demo - print to console")
    configuration_options = DemoOptionsSerializer

    def register_submission(
        self, submission: Submission, options: dict
    ) -> Tuple[str, None]:
        print(submission)
        print(options["extra_line"])
        return "demo", None

    def update_payment_status(self, submission: "Submission"):
        print(submission)


@register("failing-demo")
class DemoFailRegistration(BasePlugin):
    verbose_name = _("Demo - fail registration")
    configuration_options = DemoOptionsSerializer

    def register_submission(self, submission: Submission, options: dict) -> NoReturn:
        raise RegistrationFailed("Demo failing registration")

    def update_payment_status(self, submission: "Submission"):
        pass
