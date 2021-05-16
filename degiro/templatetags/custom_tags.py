from django import template
from degiro.utils.degiro import DeGiro

register = template.Library()

@register.simple_tag
def clientrole():
    clientDetails = DeGiro().get_client_details()
    return clientDetails['data']['clientRole'].capitalize()

@register.simple_tag
def username():
    clientDetails = DeGiro().get_client_details()
    return clientDetails['data']['username']

@register.filter
def index(sequence, position):
    return sequence[position]