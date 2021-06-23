import logging
from typing import Union

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest

from rest_framework.request import Request

from .constants import SUBMISSIONS_SESSION_KEY
from .models import Submission

logger = logging.getLogger(__name__)


def add_submmission_to_session(
    submission: Submission, request: Union[Request, HttpRequest]
) -> None:
    """
    Store the submission UUID in the request session for authorization checks.
    """
    # note: possible race condition with concurrent requests
    submissions = request.session.get(SUBMISSIONS_SESSION_KEY, [])
    submissions.append(str(submission.uuid))
    request.session[SUBMISSIONS_SESSION_KEY] = submissions


def remove_submission_from_session(
    submission: Submission, request: Union[Request, HttpRequest]
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    id_to_check = str(submission.uuid)
    submissions = request.session.get(SUBMISSIONS_SESSION_KEY, [])
    if id_to_check in submissions:
        submissions.remove(id_to_check)
        request.session[SUBMISSIONS_SESSION_KEY] = submissions


def send_confirmation_email(submission: Submission):
    email_template = submission.form.confirmation_email_template

    to_emails = submission.get_email_confirmation_recipients(submission.data)
    if not to_emails:
        logger.warning(
            "Could not determine the recipient e-mail address for submission %d, "
            "skipping the confirmation e-mail.",
            submission.id,
        )
        return

    content = email_template.render(submission)

    send_mail(
        email_template.subject,
        content,
        settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
        to_emails,
        fail_silently=False,
        html_message=content,
    )
