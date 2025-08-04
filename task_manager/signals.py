from django.db.models.signals import post_save
from .models import Task
from django.core.mail import send_mail

def task_saved(sender, instance, update_fields, created, **kwargs):
    email_recipient = [instance.owner.email]
    need_send = False
    if created:
        mail_title = 'New Task Created'
        mail_message = f'Task "{instance.title}" has been created.'
        need_send = True
    elif update_fields and 'status' in update_fields:
        mail_title = 'Task status updated'
        mail_message = f'Task status has been updated to: {instance.get_status_display()}.'
        need_send = True
        if instance.status == 'DONE':
            mail_title = 'Task closed'
            mail_message = f'Good job! Task "{instance.title}" has been closed!'
            email_recipient.extend(['crabmail@somecrab.de'])
    if need_send:
        send_mail(
            mail_title,
            mail_message,
            'crabmail@somecrab.de', # TODO: create a user with email notification@somecrab.de
            email_recipient,
        )

post_save.connect(task_saved, sender=Task)
