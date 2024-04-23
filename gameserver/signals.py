import logging

import aiohttp
from asgiref.sync import sync_to_async
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver

from gameserver.models import ContestSubmission

logger = logging.getLogger(__name__)


def is_discord(webhook: str):
    return webhook.startswith("https://discord.com/api")


def construct_discord_payload(submission: ContestSubmission) -> dict:
    BASE_URL = "https://" + Site.objects.get_current().domain

    return {
        "username": f"{submission.participation.contest.name} First Blood Notifier",
        "avatar_url": BASE_URL + "/static/favicon.png",
        "content": f"First blood on [{submission.problem.problem}]({BASE_URL + submission.problem.get_absolute_url()}) by [{submission.participation.participant}]({BASE_URL + submission.participation.participant.get_absolute_url()})!",
    }


@receiver(post_save, sender=ContestSubmission, dispatch_uid="notify_contest_firstblood")
async def my_handler(sender, instance, created, raw, using, update_fields, **kwargs):
    if not created:  # only for new submissions
        return
    if not await instance.ais_firstblooded:
        return

    if webhook := instance.participation.contest.first_blood_webhook:
        payload: dict = await sync_to_async(construct_discord_payload)(submission=instance)
        if not is_discord(webhook):
            payload = payload["content"]  # only send the content to non-discord webhooks
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook,
                json=payload,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(
                        f"Failed to send webhook: {text} - {resp.status} - {webhook} - {payload}"
                    )
