from django.utils.decorators import available_attrs
from django.utils.six import wraps
from django.views.decorators.cache import cache_page


def cache_per_user(timeout):
  def decorator(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        user_id = 'not_auth'
        if request.user.is_authenticated:
            user_id = request.user.id

        return cache_page(timeout, key_prefix="_user_{}_".format(user_id))(view_func)(request, *args, **kwargs)

    return _wrapped_view

  return decorator
